import requests
import json
import os
import zipfile
import numpy as np
from datetime import datetime
from pathlib import Path
from osgeo import gdal
import glob

class CopernicusDownloader:
    """
    Download SAFE files from Copernicus Data Space Ecosystem
    """
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1"
        self.download_url = "https://zipper.dataspace.copernicus.eu/odata/v1"
        
    def get_access_token(self):
        """Get OAuth2 access token"""
        token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
            print("✓ Authentication successful")
            return True
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    def search_product(self, product_name):
        """Search for a product by name"""
        search_url = f"{self.base_url}/Products"
        
        # Search by product name
        params = {
            "$filter": f"Name eq '{product_name}'"
        }
        
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            results = response.json()
            
            if results['value']:
                product = results['value'][0]
                print(f"✓ Found product: {product['Name']}")
                return product
            else:
                print(f"✗ Product not found: {product_name}")
                return None
        except Exception as e:
            print(f"✗ Search failed: {e}")
            return None
    
    def extract_zip(self, zip_path, output_dir):
        """Extract zip file to a shortened directory name"""
        try:
            # Create shortened directory name (first 50 chars + id)
            base_name = Path(zip_path).stem
            # Use first part before first underscore + timestamp hash
            short_name = base_name.split('_')[0][:20] + '_' + str(hash(base_name))[-8:]
            extract_dir = os.path.join(output_dir, short_name)
            
            print(f"⟳ Extracting to: {short_name}/")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"✓ Extraction complete")
            
            # Remove zip file after extraction
            os.remove(zip_path)
            print(f"✓ Removed zip file")
            
            return extract_dir
            
        except Exception as e:
            print(f"✗ Extraction failed: {e}")
            return None
    
    def tiff_to_numpy(self, tiff_path):
        """Convert TIFF to numpy array and save as .npy"""
        try:
            # Open the TIFF file
            dataset = gdal.Open(tiff_path)
            if dataset is None:
                print(f"  ✗ Could not open: {os.path.basename(tiff_path)}")
                return False
            
            # Read all bands into numpy array
            bands = []
            for i in range(1, dataset.RasterCount + 1):
                band = dataset.GetRasterBand(i)
                bands.append(band.ReadAsArray())
            
            # Stack bands if multiple, otherwise use single band
            if len(bands) > 1:
                array = np.stack(bands, axis=0)
            else:
                array = bands[0]
            
            # Save as .npy file
            npy_path = tiff_path.rsplit('.', 1)[0] + '.npy'
            np.save(npy_path, array)
            
            # Get file sizes
            tiff_size = os.path.getsize(tiff_path) / (1024**2)  # MB
            npy_size = os.path.getsize(npy_path) / (1024**2)  # MB
            
            print(f"  ✓ {os.path.basename(tiff_path)} -> .npy ({tiff_size:.1f}MB -> {npy_size:.1f}MB)")
            
            dataset = None  # Close dataset
            return True
            
        except Exception as e:
            print(f"  ✗ Conversion failed for {os.path.basename(tiff_path)}: {e}")
            return False
    
    def jp2_to_numpy(self, jp2_path):
        """Convert JP2 to numpy array and save as .npy"""
        try:
            # Open the JP2 file
            dataset = gdal.Open(jp2_path)
            if dataset is None:
                print(f"  ✗ Could not open: {os.path.basename(jp2_path)}")
                return False
            
            # Read the band into numpy array
            band = dataset.GetRasterBand(1)
            array = band.ReadAsArray()
            
            # Save as .npy file
            npy_path = jp2_path.rsplit('.', 1)[0] + '.npy'
            np.save(npy_path, array)
            
            # Get file sizes
            jp2_size = os.path.getsize(jp2_path) / (1024**2)  # MB
            npy_size = os.path.getsize(npy_path) / (1024**2)  # MB
            
            print(f"  ✓ {os.path.basename(jp2_path)} -> .npy ({jp2_size:.1f}MB -> {npy_size:.1f}MB)")
            
            dataset = None  # Close dataset
            return True
            
        except Exception as e:
            print(f"  ✗ Conversion failed for {os.path.basename(jp2_path)}: {e}")
            return False
    
    def convert_images_to_numpy(self, extract_dir, product_name):
        """Convert SAR TIFF and EO JP2 images to numpy arrays"""
        print(f"⟳ Converting images to numpy arrays...")
        
        # Determine if this is SAR or EO data
        is_sar = product_name.startswith('S1')
        is_eo = product_name.startswith('S2')
        
        converted_count = 0
        
        if is_sar:
            # SAR data: Find TIFF files in measurement folder
            measurement_dir = os.path.join(extract_dir, '**', 'measurement')
            tiff_files = glob.glob(os.path.join(measurement_dir, '*.tiff'), recursive=True)
            
            if not tiff_files:
                # Try alternative path
                tiff_files = glob.glob(os.path.join(extract_dir, '**', '*.tiff'), recursive=True)
            
            print(f"  Found {len(tiff_files)} TIFF files")
            
            for tiff_file in tiff_files:
                if self.tiff_to_numpy(tiff_file):
                    converted_count += 1
        
        elif is_eo:
            # EO data: Find JP2 files in GRANULE/*/IMG_DATA
            img_data_pattern = os.path.join(extract_dir, '**', 'GRANULE', '*', 'IMG_DATA', '*.jp2')
            jp2_files = glob.glob(img_data_pattern, recursive=True)
            
            if not jp2_files:
                # Try simpler pattern
                jp2_files = glob.glob(os.path.join(extract_dir, '**', 'IMG_DATA', '*.jp2'), recursive=True)
            
            print(f"  Found {len(jp2_files)} JP2 files")
            
            for jp2_file in jp2_files:
                if self.jp2_to_numpy(jp2_file):
                    converted_count += 1
        
        print(f"✓ Converted {converted_count} images to numpy format")
        return converted_count
    
    def download_product(self, product_id, product_name, output_dir="downloads"):
        """Download a product using its ID"""
        if not self.access_token:
            print("✗ No access token. Please authenticate first.")
            return False
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Download URL
        download_endpoint = f"{self.download_url}/Products({product_id})/$value"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        output_path = os.path.join(output_dir, f"{product_name}.zip")
        
        print(f"⟳ Downloading {product_name}...")
        
        try:
            response = requests.get(download_endpoint, headers=headers, stream=True)
            response.raise_for_status()
            
            # Get file size
            total_size = int(response.headers.get('content-length', 0))
            
            # Download with progress
            downloaded = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r  Progress: {percent:.1f}%", end='')
            
            print(f"\n✓ Downloaded: {output_path}")
            print(f"  Size: {os.path.getsize(output_path) / (1024**3):.2f} GB")
            
            # Extract the zip file
            extract_dir = self.extract_zip(output_path, output_dir)
            
            if extract_dir:
                # Convert images to numpy arrays
                self.convert_images_to_numpy(extract_dir, product_name)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Download failed: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
    
    def process_image_list(self, image_list, output_dir="downloads"):
        """Process and download multiple images from list"""
        
        # Authenticate first
        if not self.get_access_token():
            return
        
        results = []
        
        for idx, image_data in enumerate(image_list, 1):
            image_name = image_data['image_name']
            print(f"\n[{idx}/{len(image_list)}] Processing: {image_name}")
            
            # Search for product
            product = self.search_product(image_name)
            
            if product:
                # Download product
                success = self.download_product(
                    product['Id'], 
                    image_name,
                    output_dir
                )
                results.append({
                    'id': image_data['id'],
                    'image_name': image_name,
                    'status': 'success' if success else 'failed'
                })
            else:
                results.append({
                    'id': image_data['id'],
                    'image_name': image_name,
                    'status': 'not_found'
                })
        
        # Save results log
        log_file = os.path.join(output_dir, "download_log.json")
        with open(log_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'='*60}")
        print("Download Summary:")
        print(f"  Total: {len(results)}")
        print(f"  Success: {sum(1 for r in results if r['status'] == 'success')}")
        print(f"  Failed: {sum(1 for r in results if r['status'] == 'failed')}")
        print(f"  Not Found: {sum(1 for r in results if r['status'] == 'not_found')}")
        print(f"  Log saved to: {log_file}")
        print(f"{'='*60}")


# Main execution
if __name__ == "__main__":
    # Credentials
    CLIENT_ID = "sh-81987026-bee4-4509-b779-411e7ff4bbf0"
    CLIENT_SECRET = "gWvjkKZ7uIkTmGtkZnK7o1VvmOggGtWy"
    
    # Image list from your data
    IMAGE_LIST = [
        # EO Images
        {"id": 1, "image_name": "S2A_MSIL1C_20240904T151651_N0511_R025_T20TMP_20240904T221000.SAFE"}
        # {"id": 2, "image_name": "S2A_MSIL1C_20240910T153551_N0511_R111_T19TDF_20240910T204158.SAFE"},
        # {"id": 3, "image_name": "S2A_MSIL1C_20240917T152631_N0511_R068_T19TFF_20240917T203933.SAFE"},
        # {"id": 4, "image_name": "S2A_MSIL1C_20241219T153641_N0511_R111_T19TDF_20241219T172940.SAFE"},
        # {"id": 5, "image_name": "S2A_MSIL1C_20250105T070301_N0511_R063_T39PUP_20250105T085313.SAFE"},
        # {"id": 6, "image_name": "S2B_MSIL1C_20241001T160509_N0511_R054_T17RQM_20241001T204223.SAFE"},
        # {"id": 7, "image_name": "S2B_MSIL1C_20250119T160509_N0511_R054_T17RPL_20250119T210239.SAFE"},
        # {"id": 8, "image_name": "S2B_MSIL1C_20250123T154549_N0511_R111_T18RVP_20250123T204416.SAFE"},
        # {"id": 9, "image_name": "S2B_MSIL1C_20250125T161449_N0511_R140_T16RGT_20250125T194304.SAFE"},
        # {"id": 10, "image_name": "S2B_MSIL1C_20250129T160509_N0511_R054_T17RPH_20250129T193028.SAFE"},
        # # SAR Images
        # {"id": 11, "image_name": "S1A_IW_GRDH_1SDV_20241109T223334_20241109T223403_056484_06EC72_FE47.SAFE"}
        # {"id": 12, "image_name": "S1A_IW_GRDH_1SDV_20241216T231321_20241216T231346_057024_0701EF_99B1.SAFE"},
        # {"id": 13, "image_name": "S1A_IW_GRDH_1SDV_20241225T224948_20241225T225013_057155_070725_2A92.SAFE"},
        # {"id": 14, "image_name": "S1A_IW_GRDH_1SDV_20241228T231256_20241228T231321_057199_0708DD_2E21.SAFE"},
        # {"id": 15, "image_name": "S1A_IW_GRDH_1SDV_20241228T231321_20241228T231346_057199_0708DD_58EE.SAFE"},
        # {"id": 16, "image_name": "S1A_IW_GRDH_1SDV_20250313T220107_20250313T220132_058292_073499_1FF7.SAFE"},
        # {"id": 17, "image_name": "S1A_IW_GRDH_1SDV_20250313T220157_20250313T220222_058292_073499_B576.SAFE"},
        # {"id": 18, "image_name": "S1A_IW_GRDH_1SDV_20250313T220247_20250313T220312_058292_073499_E17A.SAFE"},
        # {"id": 19, "image_name": "S1A_IW_GRDH_1SDV_20250314T224134_20250314T224159_058307_073531_3174.SAFE"},
        # {"id": 20, "image_name": "S1A_IW_GRDH_1SDV_20250315T232033_20250315T232058_058322_0735BB_D696.SAFE"},
    ]
    
    # Initialize downloader
    downloader = CopernicusDownloader(CLIENT_ID, CLIENT_SECRET)
    
    # Process all images
    print("="*60)
    print("Copernicus Data Space Ecosystem - SAFE Files Downloader")
    print("="*60)
    
    # Option 1: Download all images
    downloader.process_image_list(IMAGE_LIST, output_dir="copernicus_data")
    
    # Option 2: Download single image (uncomment to use)
    # downloader.get_access_token()
    # product = downloader.search_product("S2A_MSIL1C_20240904T151651_N0511_R025_T20TMP_20240904T221000.SAFE")
    # if product:
    #     downloader.download_product(product['Id'], product['Name'])