import urllib.request
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from PIL import Image
import io
from datetime import datetime, timedelta

# 1. Fetch 24-Hour QPE from IEM WMS endpoint
wms_url = (
    "https://mesonet.agron.iastate.edu/cgi-bin/wms/us/mrms.cgi?"
    "SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=mrms_p24h"
    "&STYLES=&CRS=EPSG:4326&BBOX=31.0,-109.5,37.5,-102.5"
    "&WIDTH=1200&HEIGHT=1000&FORMAT=image/png"
)

print("Fetching New Mexico 24-Hour QPE data...")
req = urllib.request.Request(wms_url, headers={'User-Agent': 'Mozilla/5.0'})

with urllib.request.urlopen(req) as response:
    img_bytes = response.read()

overlay_img = Image.open(io.BytesIO(img_bytes))

# 2. Render Map centered on New Mexico
fig = plt.figure(figsize=(12, 10))
ax = plt.axes(projection=ccrs.PlateCarree())

ax.set_extent([-109.5, -102.5, 31.0, 37.5], crs=ccrs.PlateCarree())

# Add Boundaries
ax.add_feature(cfeature.STATES.with_scale('10m'), linewidth=1.5, edgecolor='black', zorder=3)
ax.add_feature(cfeature.COUNTIES.with_scale('10m'), linewidth=0.5, edgecolor='gray', zorder=2)
ax.set_facecolor('#e0e0e0') 

ax.imshow(overlay_img, origin='upper', extent=[-109.5, -102.5, 31.0, 37.5], transform=ccrs.PlateCarree(), zorder=1)

date_title = (datetime.utcnow() - timedelta(days=1)).strftime('%B %d, %Y')
plt.title(f"New Mexico 24-Hour Observed Precipitation (Gauge-Corrected)\nEnding {date_title} at 1200 UTC", 
          fontsize=16, fontweight='bold', pad=15)

plt.savefig("NM_24h_Rainfall.png", dpi=300, bbox_inches='tight', facecolor='white')
print("Map generated and saved as NM_24h_Rainfall.png")
