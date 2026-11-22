import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp(App)

app.use(ElementPlus)
app.use(router) // 这里非常重要，把路由挂载到整个应用中

app.mount('#app') // 挂载到 index.html 的 id="app" 的标签上
