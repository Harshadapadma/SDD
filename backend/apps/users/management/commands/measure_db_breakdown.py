import os
import sys
import time
import socket
import ssl
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

class Command(BaseCommand):
    help = "Measure exact breakdown of DNS, TCP, SSL, PgBouncer Auth, SQL Execution, and Serialization"

    def handle(self, *args, **options):
        self.stdout.write("=== DATABASE CONNECTION & QUERY TIMING BREAKDOWN ===")

        db_conf = settings.DATABASES['default']
        db_url = os.getenv('DATABASE_URL', '')
        
        host = db_conf.get('HOST') or '127.0.0.1'
        port = int(db_conf.get('PORT') or 5432)
        user = db_conf.get('USER') or ''
        password = db_conf.get('PASSWORD') or ''
        dbname = db_conf.get('NAME') or ''

        if db_url and db_url.startswith('postgres'):
            parsed = urlparse(db_url)
            host = parsed.hostname or host
            port = parsed.port or port
            user = parsed.username or user
            password = parsed.password or password
            dbname = parsed.path.lstrip('/') or dbname

        self.stdout.write(f"Target DB Host: {host}:{port} | Database: {dbname}")

        # 1. DNS Lookup
        t0 = time.time()
        try:
            ip = socket.gethostbyname(host)
            dns_time = (time.time() - t0) * 1000
            self.stdout.write(f"DNS: {dns_time:.2f} ms (IP: {ip})")
        except Exception as e:
            dns_time = (time.time() - t0) * 1000
            self.stdout.write(f"DNS Error: {e} ({dns_time:.2f} ms)")
            ip = host

        # 2. TCP Connection
        t1 = time.time()
        try:
            sock = socket.create_connection((ip, port), timeout=10)
            tcp_time = (time.time() - t1) * 1000
            self.stdout.write(f"TCP: {tcp_time:.2f} ms")
        except Exception as e:
            tcp_time = (time.time() - t1) * 1000
            self.stdout.write(f"TCP Error: {e} ({tcp_time:.2f} ms)")
            sock = None

        # 3. SSL Negotiation
        ssl_time = 0.0
        if sock:
            t2 = time.time()
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ssl_sock = ctx.wrap_socket(sock, server_hostname=host)
                ssl_time = (time.time() - t2) * 1000
                self.stdout.write(f"SSL: {ssl_time:.2f} ms")
                ssl_sock.close()
            except Exception as e:
                ssl_time = (time.time() - t2) * 1000
                self.stdout.write(f"SSL Handshake/Notice: {e} ({ssl_time:.2f} ms)")
                sock.close()

        # 4. Acquire PgBouncer / PostgreSQL Connection & Auth (psycopg2)
        t3 = time.time()
        try:
            import psycopg2
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port,
                connect_timeout=10,
                sslmode='require' if 'supabase' in host or 'render' in host else 'prefer'
            )
            pg_auth_time = (time.time() - t3) * 1000
            self.stdout.write(f"Acquire PgBouncer connection: {pg_auth_time:.2f} ms")

            # 5. Raw SQL Execution Time
            cursor = conn.cursor()
            t4 = time.time()
            cursor.execute("SELECT 1;")
            _ = cursor.fetchone()
            sql_single = (time.time() - t4) * 1000

            t5 = time.time()
            cursor.execute("SELECT COUNT(*) FROM users_user;")
            user_count = cursor.fetchone()[0]
            sql_count_time = (time.time() - t5) * 1000
            self.stdout.write(f"SQL execution (SELECT 1): {sql_single:.2f} ms")
            self.stdout.write(f"SQL execution (SELECT COUNT users_user = {user_count}): {sql_count_time:.2f} ms")

            conn.close()
        except Exception as e:
            pg_auth_time = (time.time() - t3) * 1000
            self.stdout.write(f"Acquire Connection Failed: {e} ({pg_auth_time:.2f} ms)")
            sql_single = 0.0
            sql_count_time = 0.0

        # 6. Django ORM Query Execution
        t6 = time.time()
        from apps.users.models import User
        users_list = list(User.objects.all()[:50])
        orm_time = (time.time() - t6) * 1000
        self.stdout.write(f"Django ORM Query Execution ({len(users_list)} users): {orm_time:.2f} ms")

        # 7. DRF Serialization
        t7 = time.time()
        from apps.users.serializers import UserListSerializer
        serializer_data = UserListSerializer(users_list, many=True).data
        ser_time = (time.time() - t7) * 1000
        self.stdout.write(f"Serialization: {ser_time:.2f} ms")

        self.stdout.write("==================================================")
