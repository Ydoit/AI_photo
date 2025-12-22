// src/utils/ticketFormatters.ts
import type { TicketBackend, TicketFrontend, TicketFormData } from '@/types/ticket';

// 格式化时长 (分钟 -> "xh yymin")
export const formatDuration = (minutes: number): string => {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? `${h}h ${m}min` : `${m}min`;
};

// 后端数据转前端数据
export const formatTicketToFrontend = (ticket: TicketBackend): TicketFrontend => {
  const [datePart, timePart] = ticket.date_time.split(' ');
  
  return {
    id: ticket.id,
    from: ticket.departure_station,
    to: ticket.arrival_station,
    trainCode: ticket.train_code,
    name: ticket.name || '',
    date: datePart,
    time: timePart || '',
    dateTime: ticket.date_time,
    carriage: ticket.carriage,
    seatNumber: ticket.seat_num,
    berthType: ticket.berth_type || '无',
    price: ticket.price,
    seatType: ticket.seat_type,
    discountType: ticket.discount_type || '全价票',
    totalRunningTime: ticket.total_running_time || 0,
    distance: ticket.total_mileage || 0,
    comments: ticket.comments || '',
    duration: formatDuration(ticket.total_running_time || 0),
  };
};

// 前端表单数据转后端数据
export const formatFormToBackend = (formData: TicketFormData): Partial<TicketBackend> => ({
  train_code: formData.train_code,
  departure_station: formData.from,
  arrival_station: formData.to,
  date_time: formData.dateTime,
  carriage: formData.carriage,
  seat_num: formData.seatNumber,
  berth_type: formData.berthType,
  price: formData.price,
  seat_type: formData.seatType,
  name: formData.name,
  discount_type: formData.discountType,
  total_running_time: formData.totalRunningTime || 0,
  total_mileage: formData.distance || 0,
  stop_stations: '',
  comments: formData.comments,
});

// 简单的防抖函数 (泛型)
export function debounce<T extends (...args: any[]) => any>(fn: T, delay: number = 500) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  
  const debounced = (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };

  debounced.cancel = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  };

  return debounced;
}