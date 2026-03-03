import type { 
  AnnualReportData, 
  UserInfo, 
  TimeMetrics, 
  MemoryMetrics, 
  LocationMetrics, 
  SeasonMetrics, 
  EmotionMetrics, 
  EasterEgg,
  ExpenseMetrics,
  TicketDetail,
  TravelBehaviorMetrics,
  ComprehensiveMetrics,
  TransportAnalysisMetrics
} from '@/types/annualReport';
import type { Photo } from '@/types/album';
import request from '@/utils/request';

export async function getReportExpenses(startTime: string, endTime: string): Promise<ExpenseMetrics> {
  const data = await request.get<ExpenseMetrics>('/api/annual-report/expenses', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data.data;
}

export async function getReportExpenseDetails(startTime: string, endTime: string): Promise<TicketDetail[]> {
  const retries = 2;
  let lastError;
  
  for (let i = 0; i <= retries; i++) {
    try {
      const data = await request.get<TicketDetail[]>('/api/annual-report/expenses/details', {
        params: {
            start_time: startTime,
            end_time: endTime
        }
      });
      return data.data;
    } catch (error) {
      lastError = error;
      if (i < retries) {
        // Exponential backoff or constant delay could be used here
        await new Promise(resolve => setTimeout(resolve, 500)); 
        continue;
      }
    }
  }
  throw lastError;
}

export async function getReportSummary(startTime: string, endTime: string): Promise<{user: UserInfo, time: TimeMetrics}> {
  const data = await request.get<{user: UserInfo, time: TimeMetrics}>('/api/annual-report/summary', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data.data;
}

export async function getReportMemory(startTime: string, endTime: string): Promise<MemoryMetrics> {
  const data = await request.get<MemoryMetrics>('/api/annual-report/memory', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data.data;
}

export async function getReportLocation(startTime: string, endTime: string): Promise<LocationMetrics> {
  const data = await request.get<LocationMetrics>('/api/annual-report/location', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data.data;
}

export async function getReportSeason(startTime: string, endTime: string): Promise<SeasonMetrics> {
  const data = await request.get<SeasonMetrics>('/api/annual-report/season', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data.data;
}

export async function getReportEmotion(startTime: string, endTime: string): Promise<EmotionMetrics> {
  const data = await request.get<EmotionMetrics>('/api/annual-report/emotion', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data.data;
}

export async function getReportEasterEgg(startTime: string, endTime: string): Promise<EasterEgg> {
  const data = await request.get<EasterEgg>('/api/annual-report/easter-egg', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data.data;
}

export async function getReportTravelBehavior(startTime: string, endTime: string): Promise<TravelBehaviorMetrics> {
  const data = await request.get<TravelBehaviorMetrics>('/api/annual-report/travel-behavior', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data.data;
}

export async function getReportComprehensive(startTime: string, endTime: string): Promise<ComprehensiveMetrics> {
  const data = await request.get<ComprehensiveMetrics>('/api/annual-report/comprehensive', {
    params: {
        start_time: startTime,
        end_time: endTime
    }
  });
  return data.data;
}

export async function getReportTransportAnalysis(startTime: string, endTime: string): Promise<TransportAnalysisMetrics> {
    const data = await request.get<TransportAnalysisMetrics>('/api/annual-report/transport-analysis', {
        params: {
            start_time: startTime,
            end_time: endTime
        }
    });
    return data.data;
}

export async function checkReportAvailability(year: number): Promise<{available: boolean, reason?: string}> {
    const data = await request.get<{available: boolean, reason?: string}>('/api/annual-report/check', {
        params: { year }
    });
    return data.data;
}

export async function generateReport(year: number): Promise<{success: boolean, message: string}> {
    const data = await request.post<{success: boolean, message: string}>('/api/annual-report/generate', { year });
    return data.data;
}
