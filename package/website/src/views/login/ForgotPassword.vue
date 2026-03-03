<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-4">
    <el-card class="w-full max-w-md shadow-lg">
      <template #header>
        <div class="text-center">
          <h2 class="text-xl font-bold text-gray-800 dark:text-white">找回密码</h2>
        </div>
      </template>

      <!-- Step 1: Find User -->
      <div v-if="step === 1">
        <el-form
          ref="step1FormRef"
          :model="step1Form"
          :rules="step1Rules"
          label-position="top"
          size="large"
          @submit.prevent="handleCheckUser"
        >
          <el-form-item label="用户名或邮箱" prop="username">
            <el-input 
              v-model="step1Form.username" 
              placeholder="请输入用户名或邮箱"
            />
          </el-form-item>

          <el-form-item>
            <el-button 
              type="primary" 
              class="w-full" 
              :loading="loading" 
              @click="handleCheckUser"
            >
              下一步
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Step 2: Answer Question & Reset -->
      <div v-else>
        <div class="mb-6 bg-blue-50 p-4 rounded-md border border-blue-100">
          <p class="text-sm text-gray-500 mb-1">安全问题：</p>
          <p class="text-lg font-medium text-blue-800">{{ securityQuestion }}</p>
        </div>

        <el-form
          ref="step2FormRef"
          :model="step2Form"
          :rules="step2Rules"
          label-position="top"
          size="large"
          @submit.prevent="handleResetPassword"
        >
          <el-form-item label="问题答案" prop="answer">
            <el-input 
              v-model="step2Form.answer" 
              placeholder="请输入答案"
            />
          </el-form-item>

          <el-form-item label="新密码" prop="password">
            <el-input 
              v-model="step2Form.password" 
              type="password" 
              placeholder="请输入新密码"
              show-password
            />
          </el-form-item>

          <el-form-item label="确认新密码" prop="confirmPassword">
            <el-input 
              v-model="step2Form.confirmPassword" 
              type="password" 
              placeholder="请再次输入新密码"
              show-password
            />
          </el-form-item>

          <el-form-item>
            <el-button 
              type="primary" 
              class="w-full" 
              :loading="loading" 
              @click="handleResetPassword"
            >
              重置密码
            </el-button>
          </el-form-item>
          
          <el-button link class="w-full" @click="step = 1">返回上一步</el-button>
        </el-form>
      </div>

      <div class="text-center mt-4">
        <router-link to="/login" class="text-blue-600 hover:underline text-sm">返回登录</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { authService } from '@/api/auth';

const router = useRouter();
const step = ref(1);
const loading = ref(false);
const securityQuestion = ref('');

const step1FormRef = ref<FormInstance>();
const step1Form = reactive({
  username: ''
});

const step2FormRef = ref<FormInstance>();
const step2Form = reactive({
  answer: '',
  password: '',
  confirmPassword: ''
});

const step1Rules = reactive<FormRules>({
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }]
});

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== step2Form.password) {
    callback(new Error('两次输入的密码不一致'));
  } else {
    callback();
  }
};

const step2Rules = reactive<FormRules>({
  answer: [{ required: true, message: '请输入答案', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '长度至少 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
});

const handleCheckUser = async () => {
  if (!step1FormRef.value) return;
  
  await step1FormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const res = await authService.checkResetUser({
          username_or_email: step1Form.username
        });
        securityQuestion.value = res.security_question;
        step.value = 2;
      } catch (error: any) {
        const msg = error.response?.data?.detail || '用户不存在或未设置安全问题';
        ElMessage.error(msg);
      } finally {
        loading.value = false;
      }
    }
  });
};

const handleResetPassword = async () => {
  if (!step2FormRef.value) return;
  
  await step2FormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await authService.resetPassword({
          username_or_email: step1Form.username,
          security_answer: step2Form.answer,
          new_password: step2Form.password
        });
        
        ElMessage.success('密码重置成功，请使用新密码登录');
        router.push('/login');
      } catch (error: any) {
        const msg = error.response?.data?.detail || '重置失败，请检查答案';
        ElMessage.error(msg);
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>
