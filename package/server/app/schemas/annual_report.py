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
    topPersonCount: int
    topLocation: str
    maxPhotoDay: str
    maxPhotoDayCount: int
    topFeature: str
    topFeatureCount: int

class CarouselGroup(BaseModel):
    id: str
    locationName: str
    photos: List[str]

class EmotionMetrics(BaseModel):
    starredPhotos: int
    backupPhotos: int
    totalVideoDuration: float
    totalOpenTimes: int
    starredPhotosList: List[str]
    sharedPhotosList: List[str]
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
    maxExpenseTicket: Optional[str] = None
    maxExpenseAmount: Optional[float] = 0

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
