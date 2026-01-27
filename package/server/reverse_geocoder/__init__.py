#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/12/24 10:08
@Author      : SiYuan
@Email       : sixyuan044@gmail.com
@File        : server-__init__.py.py
@Description : 
"""
from __future__ import print_function

""" A Fast, Offline Reverse Geocoder in Python

A Python library for offline reverse geocoding. It improves on an existing library
called reverse_geocode developed by Richard Penman.
"""

__author__ = 'Ajay Thampi'
import os
import sys
import csv
import gc
if sys.platform == 'win32':
    # Windows C long is 32 bits, and the Python int is too large to fit inside.
    # Use the limit appropriate for a 32-bit integer as the max file size
    csv.field_size_limit(2**31-1)
else:
    csv.field_size_limit(sys.maxsize)
import glob
import zipfile

from scipy.spatial import cKDTree as KDTree
from reverse_geocoder import cKDTree_MP as KDTree_MP
import numpy as np

GN_URL = 'http://download.geonames.org/export/dump/'
GN_CITIES1000 = 'JP'
GN_ADMIN1 = 'admin1CodesASCII.txt'
GN_ADMIN2 = 'admin2Codes.txt'

# Schema of the GeoNames Cities with Population > 1000
GN_COLUMNS = {
    'geoNameId': 0,
    'name': 1,
    'asciiName': 2,
    'alternateNames': 3,
    'latitude': 4,
    'longitude': 5,
    'featureClass': 6,
    'featureCode': 7,
    'countryCode': 8,
    'cc2': 9,
    'admin1Code': 10,
    'admin2Code': 11,
    'admin3Code': 12,
    'admin4Code': 13,
    'population': 14,
    'elevation': 15,
    'dem': 16,
    'timezone': 17,
    'modificationDate': 18
}

# Schema of the GeoNames Admin 1/2 Codes
ADMIN_COLUMNS = {
    'concatCodes': 0,
    'name': 1,
    'asciiName': 2,
    'geoNameId': 3
}


# Schema of the cities file created by this library
RG_COLUMNS = [
    'longitude','latitude','country','admin_1','admin_2','admin_3','admin_4'
]

# Name of cities file created by this library
RG_FILE = f'rg_cities1000_{GN_CITIES1000}.csv'
# RG_FILE = 'rg_cities_cn.csv'

# WGS-84 major axis in kms
A = 6378.137

# WGS-84 eccentricity squared
E2 = 0.00669437999014

def load_admin_codes(output_dir, verbose=True):
    if verbose:
        print('Loading admin codes...')
    
    admin1_file = os.path.join(output_dir, GN_ADMIN1)
    admin2_file = os.path.join(output_dir, GN_ADMIN2)
    
    admin1_map = {}
    if os.path.exists(admin1_file):
        t_rows = csv.reader(open(admin1_file, 'rt', encoding='utf-8'), delimiter='\t')
        for row in t_rows:
            admin1_map[row[ADMIN_COLUMNS['concatCodes']]] = row[ADMIN_COLUMNS['asciiName']]
            
    admin2_map = {}
    if os.path.exists(admin2_file):
        for row in csv.reader(open(admin2_file, 'rt', encoding='utf-8'), delimiter='\t'):
            admin2_map[row[ADMIN_COLUMNS['concatCodes']]] = row[ADMIN_COLUMNS['asciiName']]
            
    return admin1_map, admin2_map

def convert_geonames_to_csv(txt_path, csv_path, admin1_map, admin2_map, verbose=True):
    if verbose:
        print(f'Creating formatted geocoded file {csv_path}...')
        
    writer = csv.DictWriter(open(csv_path, 'wt', encoding='utf-8', newline=''), fieldnames=RG_COLUMNS)
    writer.writeheader()
    
    rows = []
    with open(txt_path, 'rt', encoding='utf-8') as fin:
        reader = csv.reader(fin, delimiter='\t', quoting=csv.QUOTE_NONE)
        for row in reader:
            lat = row[GN_COLUMNS['latitude']]
            lon = row[GN_COLUMNS['longitude']]
            name = row[GN_COLUMNS['asciiName']]
            cc = row[GN_COLUMNS['countryCode']]

            admin1_c = row[GN_COLUMNS['admin1Code']]
            admin2_c = row[GN_COLUMNS['admin2Code']]
            admin3_c = row[GN_COLUMNS['admin3Code']]
            admin4_c = row[GN_COLUMNS['admin4Code']]

            cc_admin1 = cc+'.'+admin1_c
            cc_admin2 = cc+'.'+admin1_c+'.'+admin2_c

            admin1 = ''
            admin2 = ''

            if cc_admin1 in admin1_map:
                admin1 = admin1_map[cc_admin1]
            if cc_admin2 in admin2_map:
                admin2 = admin2_map[cc_admin2]

            write_row = {
                'latitude': lat,
                'longitude': lon,
                'country': cc,
                'admin_1': admin1,
                'admin_2': admin2,
                'admin_3': name,
                'admin_4': admin4_c,
            }
            rows.append(write_row)
    
    writer.writerows(rows)

def download_file(url, local_path, verbose=True):
    if not os.path.exists(local_path):
        if verbose:
            print(f'Downloading {url} to {local_path}...')
        try: # Python 3
            import urllib.request
            urllib.request.urlretrieve(url, local_path)
        except ImportError: # Python 2
            import urllib
            urllib.urlretrieve(url, local_path)

def download_country_data(country_code, output_dir, verbose=True):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Ensure admin files exist
    admin1_path = os.path.join(output_dir, GN_ADMIN1)
    admin2_path = os.path.join(output_dir, GN_ADMIN2)
    
    download_file(GN_URL + GN_ADMIN1, admin1_path, verbose)
    download_file(GN_URL + GN_ADMIN2, admin2_path, verbose)
    
    # Download country zip
    zip_filename = f'{country_code}.zip'
    zip_path = os.path.join(output_dir, zip_filename)
    txt_filename = f'{country_code}.txt'
    
    try:
        download_file(GN_URL + zip_filename, zip_path, verbose)
    except Exception as e:
        print(f"Error downloading {country_code}: {e}")
        return

    # Extract
    if verbose:
        print(f'Extracting {zip_filename}...')
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extract(txt_filename, output_dir)
        
    # Convert
    admin1_map, admin2_map = load_admin_codes(output_dir, verbose)
    txt_path = os.path.join(output_dir, txt_filename)
    csv_path = os.path.join(output_dir, f'{country_code}.csv')
    
    convert_geonames_to_csv(txt_path, csv_path, admin1_map, admin2_map, verbose)
    
    # Cleanup
    if os.path.exists(txt_path):
        os.remove(txt_path)
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    if verbose:
        print(f'Successfully processed {country_code} to {csv_path}')

def singleton(cls):
    """
    Function to get single instance of the RGeocoder class
    """
    instances = {}
    def getinstance(**kwargs):
        """
        Creates a new RGeocoder instance if not created already
        """
        if cls not in instances:
            instances[cls] = cls(**kwargs)
        return instances[cls]
    return getinstance

@singleton
class RGeocoder(object):
    """
    The main reverse geocoder class
    """
    def __init__(self, mode=1, verbose=True, stream=None, data_dir=None):
        """ Class Instantiation
        Args:
        mode (int): Library supports the following two modes:
                    - 1 = Single-threaded K-D Tree
                    - 2 = Multi-threaded K-D Tree (Default)
        verbose (bool): For verbose output, set to True
        stream (io.StringIO): An in-memory stream of a custom data source
        data_dir (str): Directory containing CSV files to load
        """
        self.mode = mode
        self.verbose = verbose
        self.stream = stream
        self.data_dir = data_dir
        self.tree = None
        self.locations = None
        # Lazy load: Data will be loaded on first query

    def _load_data(self):
        """ Helper to load data if not already loaded """
        coordinates = []
        self.locations = []

        if self.stream:
            if hasattr(self.stream, 'seek'):
                self.stream.seek(0)
            coords, locs = self.load(self.stream)
            coordinates.extend(coords)
            self.locations.extend(locs)
        elif self.data_dir:
            if not os.path.exists(self.data_dir):
                if self.verbose:
                    print(f"Data directory {self.data_dir} does not exist.")
            else:
                files = glob.glob(os.path.join(self.data_dir, '*.csv'))
                if not files and self.verbose:
                     print(f"No CSV files found in {self.data_dir}")
                
                for f in files:
                    if self.verbose:
                        print(f"Loading {f}...")
                    try:
                        with open(f, 'rt', encoding='utf-8') as fin:
                            coords, locs = self.load(fin)
                            coordinates.extend(coords)
                            self.locations.extend(locs)
                    except Exception as e:
                        print(f"Failed to load {f}: {e}")
        else:
            coords, locs = self.extract(rel_path(RG_FILE))
            coordinates.extend(coords)
            self.locations.extend(locs)

        if not coordinates:
            if self.verbose:
                print("No data loaded.")
            return

        if self.mode == 1: # Single-process
            self.tree = KDTree(coordinates)
        else: # Multi-process
            self.tree = KDTree_MP.cKDTree_MP(coordinates)

    def unload(self):
        """ Release memory used by KDTree and locations """
        self.tree = None
        self.locations = None
        gc.collect()

    def query(self, coordinates):
        """
        Function to query the K-D tree to find the nearest city
        Args:
        coordinates (list): List of tuple coordinates, i.e. [(latitude, longitude)]
        """
        if self.tree is None:
            self._load_data()

        if self.mode == 1:
            _, indices = self.tree.query(coordinates, k=1)
        else:
            _, indices = self.tree.pquery(coordinates, k=1)
        return [self.locations[index] for index in indices]

    def load(self, stream):
        """
        Function that loads a custom data source
        Args:
        stream (io.StringIO): An in-memory stream of a custom data source.
                              The format of the stream must be a comma-separated file
                              with header containing the columns defined in RG_COLUMNS.
        """
        stream_reader = csv.DictReader(stream, delimiter=',')
        header = stream_reader.fieldnames

        if header != RG_COLUMNS:
            raise csv.Error('Input must be a comma-separated file with header containing ' + \
                'the following columns - %s. For more help, visit: ' % (','.join(RG_COLUMNS)) + \
                'https://github.com/thampiman/reverse-geocoder')

        # Load all the coordinates and locations
        geo_coords, locations = [], []
        for row in stream_reader:
            geo_coords.append((row['latitude'], row['longitude']))
            locations.append(row)

        return geo_coords, locations

    def extract(self, local_filename):
        """
        Function loads the already extracted GeoNames cities file or downloads and extracts it if
        it doesn't exist locally
        Args:
        local_filename (str): Path to local RG_FILE
        """
        if os.path.exists(local_filename):
            if self.verbose:
                print('Loading formatted geocoded file...')
            rows = csv.DictReader(open(local_filename, 'rt', encoding='utf-8'))
        else:
            gn_cities1000_url = GN_URL + GN_CITIES1000 + '.zip'
            gn_admin1_url = GN_URL + GN_ADMIN1
            gn_admin2_url = GN_URL + GN_ADMIN2

            cities1000_zipfilename = GN_CITIES1000 + '.zip'
            cities1000_filename = GN_CITIES1000 + '.txt'

            if not os.path.exists(cities1000_zipfilename):
                if self.verbose:
                    print('Downloading files from Geoname...')
                try: # Python 3
                    import urllib.request
                    urllib.request.urlretrieve(gn_cities1000_url, cities1000_zipfilename)
                    urllib.request.urlretrieve(gn_admin1_url, GN_ADMIN1)
                    urllib.request.urlretrieve(gn_admin2_url, GN_ADMIN2)
                except ImportError: # Python 2
                    import urllib
                    urllib.urlretrieve(gn_cities1000_url, cities1000_zipfilename)
                    urllib.urlretrieve(gn_admin1_url, GN_ADMIN1)
                    urllib.urlretrieve(gn_admin2_url, GN_ADMIN2)


            if self.verbose:
                print('Extracting cities1000...')
            _z = zipfile.ZipFile(open(cities1000_zipfilename, 'rb'))
            open(cities1000_filename, 'wb').write(_z.read(cities1000_filename))

            if self.verbose:
                print('Loading admin1 codes...')
            admin1_map = {}
            t_rows = csv.reader(open(GN_ADMIN1, 'rt', encoding='utf-8'), delimiter='\t')
            for row in t_rows:
                admin1_map[row[ADMIN_COLUMNS['concatCodes']]] = row[ADMIN_COLUMNS['asciiName']]

            if self.verbose:
                print('Loading admin2 codes...')
            admin2_map = {}
            for row in csv.reader(open(GN_ADMIN2, 'rt', encoding='utf-8'), delimiter='\t'):
                admin2_map[row[ADMIN_COLUMNS['concatCodes']]] = row[ADMIN_COLUMNS['asciiName']]

            if self.verbose:
                print('Creating formatted geocoded file...')
            writer = csv.DictWriter(open(local_filename, 'wt', encoding='utf-8', newline=''), fieldnames=RG_COLUMNS)
            rows = []
            for row in csv.reader(open(cities1000_filename, 'rt', encoding='utf-8'), \
                    delimiter='\t', quoting=csv.QUOTE_NONE):
                lat = row[GN_COLUMNS['latitude']]
                lon = row[GN_COLUMNS['longitude']]
                name = row[GN_COLUMNS['asciiName']]
                cc = row[GN_COLUMNS['countryCode']]

                admin1_c = row[GN_COLUMNS['admin1Code']]
                admin2_c = row[GN_COLUMNS['admin2Code']]
                admin3_c = row[GN_COLUMNS['admin3Code']]
                admin4_c = row[GN_COLUMNS['admin4Code']]

                cc_admin1 = cc+'.'+admin1_c
                cc_admin2 = cc+'.'+admin1_c+'.'+admin2_c

                admin1 = ''
                admin2 = ''

                if cc_admin1 in admin1_map:
                    admin1 = admin1_map[cc_admin1]
                if cc_admin2 in admin2_map:
                    admin2 = admin2_map[cc_admin2]

                write_row = {'latitude':lat,
                             'longitude':lon,
                             'country': cc,
                             'admin_1':admin1,
                             'admin_2':admin2,
                            'admin_3':name,
                            'admin_4':admin4_c,
                             }
                rows.append(write_row)
            writer.writeheader()
            writer.writerows(rows)

            if self.verbose:
                print('Removing extracted cities1000 to save space...')
            os.remove(cities1000_filename)

        # Load all the coordinates and locations
        geo_coords, locations = [], []
        for row in rows:
            geo_coords.append((row['latitude'], row['longitude']))
            locations.append(row)
        return geo_coords, locations

def geodetic_in_ecef(geo_coords):
    geo_coords = np.asarray(geo_coords).astype(np.float)
    lat = geo_coords[:, 0]
    lon = geo_coords[:, 1]

    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    normal = A / (np.sqrt(1 - E2 * (np.sin(lat_r) ** 2)))

    x = normal * np.cos(lat_r) * np.cos(lon_r)
    y = normal * np.cos(lat_r) * np.sin(lon_r)
    z = normal * (1 - E2) * np.sin(lat)

    return np.column_stack([x, y, z])

def rel_path(filename):
    """
    Function that gets relative path to the filename
    """
    return os.path.join(os.getcwd(), os.path.dirname(__file__), filename)

def get(geo_coord, mode=1, verbose=True, data_dir=None):
    """
    Function to query for a single coordinate
    """
    if not isinstance(geo_coord, tuple) or not isinstance(geo_coord[0], float):
        raise TypeError('Expecting a tuple')

    _rg = RGeocoder(mode=mode, verbose=verbose)
    return _rg.query([geo_coord])[0]

def search(geo_coords, mode=1, verbose=True, data_dir=None):
    """
    Function to query for a list of coordinates
    """
    if not isinstance(geo_coords, tuple) and not isinstance(geo_coords, list):
        raise TypeError('Expecting a tuple or a tuple/list of tuples')
    elif not isinstance(geo_coords[0], tuple):
        geo_coords = [geo_coords]

    _rg = RGeocoder(mode=mode, verbose=verbose, data_dir=data_dir)
    return _rg.query(geo_coords)

def unload():
    """
    Function to release memory used by RGeocoder singleton
    """
    # Since RGeocoder is a singleton, instantiating it returns the existing instance
    # Calling unload() on it will release resources
    # If it hasn't been instantiated yet, it creates a lightweight instance (no data loaded) and unloads it (no-op)
    RGeocoder().unload()

if __name__ == '__main__':
    # 1. 下载中国数据到 'my_data' 目录
    # download_country_data('CN', 'my_data')

    # 2. 从 'my_data' 目录加载数据进行反向地理编码
    geocoder = RGeocoder(data_dir='my_data')
    result = geocoder.query([(39.9042, 116.4074)])  # 北京坐标
    print(result)
    print('Testing single coordinate through get...')
    city = (37.78674, -122.39222)
    city = (35.6895, 139.6917)
    # city = (34.0522, -118.2437)
    print('Reverse geocoding 1 city...')
    result = get(city)
    print(result)

    print('Testing coordinates...')
    cities = [(51.5214588, -0.1729636), (9.936033, 76.259952), (37.38605, -122.08385)]
    print('Reverse geocoding %d cities...' % len(cities))
    results = search(cities)
    print(results)
