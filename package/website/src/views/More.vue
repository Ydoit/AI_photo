<template>
  <div class="min-h-screen bg-[#f3f5f7] flex items-center justify-center p-4">
    <!-- 自定义火车票 -->
    <TrainTicket
      class="mt-8"
      serial="283K104567"
      gate="5A"
      fromStation="上海虹桥"
      fromPinyin="Shanghaihongqiao"
      toStation="南京南"
      toPinyin="Nanjingnan"
      trainCode="G2025"
      dateTime="2023年10月01日 08:30"
      carriage="07"
      seatNumber="12F"
      price="443.5"
      seatType="一等座"
      idNumber="3201021990****5678"
      passengerName="张三"
      footerInfo="65773311920607K104567　北京南售"
    />
  </div>
</template>

<script setup>
import TrainTicket from '@/components/TrainTicket.vue';
</script>