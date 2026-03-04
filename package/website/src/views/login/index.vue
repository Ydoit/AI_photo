<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-4">
    <el-card class="w-full max-w-md shadow-lg">
      <template #header>
        <div class="text-center">
          <h2 class="text-xl font-bold text-gray-800 dark:text-white">登录 TrailSnap</h2>
        </div>
      </template>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="请输入用户名"
            :prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <div class="flex items-center justify-between mb-4">
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
          <router-link to="/forgot-password" class="text-sm text-blue-600 hover:underline">忘记密码?</router-link>
        </div>

        <el-form-item>
          <el-button 
            type="primary" 
            class="w-full" 
            :loading="loading" 
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>

        <div class="text-center mt-4">
          <span class="text-gray-600 text-sm">还没有账号? </span>
          <router-link to="/register" class="text-blue-600 hover:underline text-sm">立即注册</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '@/stores/user';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { User, Lock } from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const loginFormRef = ref<FormInstance>();
const loading = ref(false);
const rememberMe = ref(false);

const loginForm = reactive({
  username: '',
  password: ''
});

const rules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名长度至少为 3 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为 6 个字符', trigger: 'blur' }
  ]
});

onMounted(() => {
  const savedUsername = localStorage.getItem('remember_username');
  if (savedUsername) {
    loginForm.username = savedUsername;
    rememberMe.value = true;
  }
});

const handleLogin = async () => {
  if (!loginFormRef.value) return;
  
  await loginFormRef.value.validate(async (valid, fields) => {
    if (valid) {
      loading.value = true;
      try {
        await userStore.login(loginForm);

        if (rememberMe.value) {
          localStorage.setItem('remember_username', loginForm.username);
        } else {
          localStorage.removeItem('remember_username');
        }

        ElMessage.success('登录成功');

        // Redirect to previous page or home
        const redirect = route.query.redirect as string || '/';
        router.push(redirect);
      } catch (error: any) {
        console.error(error);
        // Extract error message if available from backend response structure
        const msg = error.response?.data?.detail || error.message || '登录失败，请检查用户名和密码';
        ElMessage.error(msg);
      } finally {
        loading.value = false;
      }
    } else {
      console.log('error submit!', fields);
    }
  });
};
</script>

<style scoped>
/* Scoped styles if needed */
</style>
