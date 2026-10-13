import urllib.request
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from PIL import Image
import io
from datetime import datetime, timedelta
import numpy as np

# 1. Fetch 24-Hour QPE Data from IEM WMS
wms_url = (
    "https://mesonet.agron.iastate.edu/cgi-bin/wms/us/mrms.cgi?"
    "SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=mrms_p24h"
    "&STYLES=&CRS=EPSG:4326&BBOX=31.0,-109.5,37.5,-102.5"
    "&WIDTH=1600&HEIGHT=1400&FORMAT=image/png"
)

print("Fetching New Mexico QPE raster data...")
req = urllib.request.Request(wms_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    img_bytes = response.read()

overlay_img = Image.open(io.BytesIO(img_bytes))

# 2. Setup Figure & Map Projection
fig = plt.figure(figsize=(14, 12), dpi=300)
ax = plt.axes([0.0, 0.05, 1.0, 0.88], projection=ccrs.PlateCarree())
ax.set_extent([-109.5, -102.5, 31.0, 37.5], crs=ccrs.PlateCarree())

# Terrain / Gray Background for Zero Rainfall
ax.set_facecolor('#dcd6cd') 

# Add Boundaries (State Lines & Counties)
counties = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_2_counties',
    scale='10m',
    facecolor='none'
)

ax.add_feature(counties, linewidth=0.6, edgecolor='black', zorder=3)
ax.add_feature(cfeature.STATES.with_scale('10m'), linewidth=2.0, edgecolor='black', zorder=4)

# Overlay QPE Layer
ax.imshow(overlay_img, origin='upper', extent=[-109.5, -102.5, 31.0, 37.5], 
          transform=ccrs.PlateCarree(), zorder=2)

# 3. Create Custom Vertical Colorbar Legend matching NWS San Antonio Style
nws_colors = [
    '#7be382', '#38a800', '#267300', # Greens (0.01 - 0.5")
    '#ffff00', '#ffaa00', '#ff5500', # Yellow/Gold/Orange (0.5 - 2.0")
    '#e60000', '#980000', '#730000'  # Reds / Magenta (3.0" - 8.0"+)
]
levels = [0.01, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
cmap = ListedColormap(nws_colors)
norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)

# Add Vertical Inset Colorbar on Left Side
cax = fig.add_axes([0.03, 0.15, 0.025, 0.65], facecolor='#111111') # Dark translucent box
cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation='vertical')
cbar.set_label('Est. Precipitation (in)', color='white', fontsize=12, fontweight='bold', labelpad=10)
cbar.ax.yaxis.set_tick_params(color='white')
plt.setp(plt.getp(cbar.ax, 'yticklabels'), color='white', fontweight='bold', fontsize=10)

# 4. Top Header Banner (Dark NWS Banner)
now = datetime.utcnow()
yesterday = now - timedelta(days=1)
valid_start = yesterday.strftime('%m/%d/%Y 07:00 AM MDT')
valid_end = now.strftime('%m/%d/%Y 07:00 AM MDT')
issued_time = now.strftime('%b %d, %Y %I:%M %p MDT')

header_ax = fig.add_axes([0.0, 0.93, 1.0, 0.07], facecolor='#09182b')
header_ax.axis('off')
header_ax.text(0.02, 0.60, "24-Hour Estimated Rainfall", color='white', fontsize=22, fontweight='bold', va='center')
header_ax.text(0.02, 0.22, f"Valid: {valid_start} - {valid_end}", color='#dcdcdc', fontsize=12, va='center')

header_ax.text(0.98, 0.60, "Weather Forecast Office", color='white', fontsize=11, ha='right', va='center')
header_ax.text(0.98, 0.22, f"Albuquerque, NM | Issued {issued_time}", color='#dcdcdc', fontsize=10, ha='right', va='center')

# 5. Footer Banner
footer_ax = fig.add_axes([0.0, 0.0, 1.0, 0.05], facecolor='#09182b')
footer_ax.axis('off')
footer_ax.text(0.02, 0.5, "NWSAlbuquerque", color='white', fontsize=12, fontweight='bold', va='center')
footer_ax.text(0.98, 0.5, "weather.gov/abq", color='white', fontsize=12, fontweight='bold', ha='right', va='center')

# Save Output
output_file = "NM_24h_Rainfall.png"
plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
print(f"Professional NWS-styled map saved successfully to {output_file}")
