import re

def process_file(filepath, prefix):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Template Replacements
    content = content.replace('name="panel"', f'name="{prefix}-panel"')
    content = content.replace('class="notif-panel"', f'class="{prefix}-notif-panel"')
    content = content.replace('class="panel-header"', f'class="{prefix}-panel-header"')
    content = content.replace('class="panel-title', f'class="{prefix}-panel-title')
    content = content.replace('class="panel-actions"', f'class="{prefix}-panel-actions"')
    content = content.replace('class="panel-icon-btn"', f'class="{prefix}-panel-icon-btn"')
    content = content.replace('class="muted-banner"', f'class="{prefix}-muted-banner"')
    content = content.replace('class="panel-body"', f'class="{prefix}-panel-body"')
    content = content.replace('class="panel-empty"', f'class="{prefix}-panel-empty"')
    content = content.replace("'panel-item'", f"'{prefix}-panel-item'")
    content = content.replace('class="panel-item-icon"', f'class="{prefix}-panel-item-icon"')
    content = content.replace('class="panel-item-body"', f'class="{prefix}-panel-item-body"')
    content = content.replace('class="panel-item-header"', f'class="{prefix}-panel-item-header"')
    content = content.replace('class="panel-item-title"', f'class="{prefix}-panel-item-title"')
    content = content.replace('class="panel-item-time"', f'class="{prefix}-panel-item-time"')
    content = content.replace('class="panel-item-msg"', f'class="{prefix}-panel-item-msg"')
    content = content.replace('class="panel-unread-dot"', f'class="{prefix}-panel-unread-dot"')
    content = content.replace('class="toast-stack"', f'class="{prefix}-toast-stack"')
    content = content.replace("'toast'", f"'{prefix}-toast'")
    content = content.replace('class="toast-icon"', f'class="{prefix}-toast-icon"')
    content = content.replace('class="toast-body"', f'class="{prefix}-toast-body"')
    content = content.replace('class="toast-title"', f'class="{prefix}-toast-title"')
    content = content.replace('class="toast-msg"', f'class="{prefix}-toast-msg"')
    content = content.replace('class="toast-close"', f'class="{prefix}-toast-close"')

    # CSS Replacements
    content = content.replace('.notif-panel', f'.{prefix}-notif-panel')
    content = content.replace('.panel-enter', f'.{prefix}-panel-enter')
    content = content.replace('.panel-leave', f'.{prefix}-panel-leave')
    content = content.replace('.panel-header', f'.{prefix}-panel-header')
    content = content.replace('.panel-title', f'.{prefix}-panel-title')
    content = content.replace('.panel-actions', f'.{prefix}-panel-actions')
    content = content.replace('.panel-icon-btn', f'.{prefix}-panel-icon-btn')
    content = content.replace('.muted-banner', f'.{prefix}-muted-banner')
    content = content.replace('.panel-body', f'.{prefix}-panel-body')
    content = content.replace('.panel-empty', f'.{prefix}-panel-empty')
    content = content.replace('.panel-item', f'.{prefix}-panel-item')
    content = content.replace('.panel-unread-dot', f'.{prefix}-panel-unread-dot')
    content = content.replace('.toast-stack', f'.{prefix}-toast-stack')
    content = content.replace('.toast', f'.{prefix}-toast')

    # Variables & Keyframes
    content = content.replace('--accent', f'--{prefix}-accent')
    content = content.replace('--t-accent', f'--{prefix}-t-accent')
    content = content.replace('toastIn', f'{prefix}toastIn')
    content = content.replace('toastOut', f'{prefix}toastOut')
    content = content.replace('toastEnter', f'{prefix}toastEnter')
    content = content.replace('toastLeave', f'{prefix}toastLeave')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"{filepath} updated")

process_file('src/Layouts/AdminLayout.vue', 'a')
process_file('src/Layouts/UserLayout.vue', 'u')
