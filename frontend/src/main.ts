import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import '@fortawesome/fontawesome-free/css/all.css';

import "./styles/base/_variables.css"; // we'll create this next

createApp(App)
  .use(router)
  .mount("#app");