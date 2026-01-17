from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.schemas.photo import Photo


class UserInfo(BaseModel):
    nickname: str
    avatarUrl: str

class TimeMetrics(BaseModel):
    totalPhotos: int
    accompanyDays: int
    firstPhotoDate: Optional[str] = None
    lastPhotoDate: Optional[str] = None
    lateNightPhotoCount: Optional[int] = 0
    photoDates: List[str] = []

class CategoryDistributionItem(BaseModel):
    name: str
    value: int

class MemoryMetrics(BaseModel):
    categoryDistribution: List[CategoryDistributionItem]
    topPersonName: str
    topPersonCount: int
    topLocation: str
    maxPhotoDay: str
    maxPhotoDayCount: int
    topFeature: str
    topFeatureCount: int
    topMake: str
    topModel: str
    topMakeModelCount: int

class CarouselGroup(BaseModel):
    id: str
    locationName: str
    photos: List[str]

class EmotionMetrics(BaseModel):
    livePhotos: int
    backupPhotos: int
    totalVideoDuration: float
    cameraPhotos: int
    emotionCarouselGroups: List[CarouselGroup]

class TopCity(BaseModel):
    cityName: str
    photoCount: int
    provinceName: str

class LocationPoint(BaseModel):
    lng: float
    lat: float
    name: str
    count: int
    coverUrl: Optional[str] = None

class LocationMetrics(BaseModel):
    lightenProvinceNum: int
    lightenCityNum: int
    topCities: List[TopCity]
    locationPoints: List[LocationPoint]
    farthestCity: Optional[str] = None
    farthestDistance: Optional[int] = 0
    farthestCityPhotos: List[Photo] = []

class SeasonData(BaseModel):
    seasonName: str
    photoCount: int
    topTag: str
    representativePhoto: str
    highlight: str
    shootMonth: str

class SeasonMetrics(BaseModel):
    seasonList: List[SeasonData]

class MonthlyExpense(BaseModel):
    month: str
    amount: float

class ExpenseMetrics(BaseModel):
    totalAmount: float
    totalCount: int
    averagePrice: float
    monthlyTrend: List[MonthlyExpense]
    totalAmountLastYear: Optional[float] = 0.0
    monthlyTrendLastYear: List[MonthlyExpense] = []
    maxExpenseTicket: Optional[str] = None
    maxExpenseAmount: Optional[float] = 0

class MonthlyFrequency(BaseModel):
    month: str
    count: int

class RouteStats(BaseModel):
    route: str
    count: int

class DestinationStats(BaseModel):
    city: str
    count: int

class TripTypeDistribution(BaseModel):
    workday: int
    weekend: int
    holiday: int

class TravelBehaviorMetrics(BaseModel):
    monthlyFrequency: List[MonthlyFrequency]
    topRoutes: List[RouteStats]
    topDestinations: List[DestinationStats]
    tripTypeDistribution: TripTypeDistribution

class ComprehensiveMetrics(BaseModel):
    totalMileage: int
    costPerKm: float

class TransportAnalysisMetrics(BaseModel):
    behavior: TravelBehaviorMetrics
    comprehensive: ComprehensiveMetrics

class TicketDetail(BaseModel):
    id: str
    train_code: str
    departure_station: str
    arrival_station: str
    date_time: datetime
    price: float
    seat_type: str
    name: str

class EasterEggTags(BaseModel):
    main: str
    sub: List[str]

class EasterEgg(BaseModel):
    bestPhotoUrl: str
    bestPhotoDate: str
    tags: EasterEggTags

class AnnualReportData(BaseModel):
    year: int
    user: UserInfo
    time: TimeMetrics
    memory: MemoryMetrics
    emotion: EmotionMetrics
    location: LocationMetrics
    season: SeasonMetrics
    easterEgg: EasterEgg
    expense: Optional[ExpenseMetrics] = None
    travelBehavior: Optional[TravelBehaviorMetrics] = None
    comprehensive: Optional[ComprehensiveMetrics] = None
    transportAnalysis: Optional[TransportAnalysisMetrics] = None
