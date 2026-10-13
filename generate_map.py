import urllib.request
import rioxarray
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime, timedelta, timezone
import os

# 1. Fetch Yesterday's Gauge-Corrected 24-Hour QPE (Iowa State Mesonet Archive)
now = datetime.now(timezone.utc)
yesterday = now - timedelta(days=1)
date_str = yesterday.strftime('%Y%m%d')

tif_url = f"https://mesonet.agron.iastate.edu/archive/data/{yesterday.year}/{yesterday.strftime('%m')}/{yesterday.strftime('%d')}/GIS/mrms/p24h_{date_str}1200.tif"
tif_filename = "mrms_24h.tif"

print(f"Downloading 24-Hour QPE GeoTIFF for {date_str}...")
req = urllib.request.Request(tif_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    with open(tif_filename, 'wb') as f:
        f.write(response.read())

# 2. Process GeoTIFF Grid & Clip to New Mexico Bounding Box
da = rioxarray.open_rasterio(tif_filename)
da_nm = da[0].rio.clip_box(minx=-109.6, miny=31.0, maxx=-102.4, maxy=37.6)

# Convert millimeters to inches
precip_inches = da_nm / 25.4
precip_inches = precip_inches.where(precip_inches >= 0.01)

# 3. Exact NWS San Antonio Color Ramp & Levels
nws_colors = [
    '#d7f3d6', '#7be382', '#38a800', '#267300',  # Light Greens -> Dark Greens (0.01 - 0.5")
    '#ffff00', '#ffaa00', '#ff5500',              # Yellows / Oranges (0.5 - 2.0")
    '#e60000', '#980000', '#730000',              # Bright Red -> Deep Reds (2.0 - 6.0")
    '#4a0000'                                    # Dark Maroon/Purple (6.0 - 8.0"+)
]
levels = [0.01, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
cmap = ListedColormap(nws_colors)
norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)

# 4. Canvas Setup & Map Extent
fig = plt.figure(figsize=(12, 10), dpi=300)

# Main map canvas [left, bottom, width, height]
ax = fig.add_axes([0.0, 0.04, 1.0, 0.88], projection=ccrs.PlateCarree())
ax.set_extent([-109.5, -102.5, 31.0, 37.5], crs=ccrs.PlateCarree())

# Warm terrain background for dry regions
ax.set_facecolor('#e8e3d8')

# Add Natural Earth Boundaries
counties = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_2_counties',
    scale='10m',
    facecolor='none'
)
ax.add_feature(counties, linewidth=0.6, edgecolor='#333333', zorder=3)
ax.add_feature(cfeature.STATES.with_scale('10m'), linewidth=2.0, edgecolor='black', zorder=4)

# 5. Smooth Contour Plotting
lons, lats = np.meshgrid(da_nm.x.values, da_nm.y.values)
cf = ax.contourf(
    lons, lats, precip_inches.values,
    levels=levels,
    cmap=cmap,
    norm=norm,
    transform=ccrs.PlateCarree(),
    extend='max',
    zorder=2
)

# 6. Add Major New Mexico Cities
cities = {
    'Albuquerque': (-106.6504, 35.0844),
    'Santa Fe': (-105.9378, 35.6870),
    'Las Cruces': (-106.7777, 32.3199),
    'Roswell': (-104.5230, 33.3943),
    'Farmington': (-108.2187, 36.7281),
    'Gallup': (-108.7426, 35.5281)
}

for name, (lon, lat) in cities.items():
    ax.plot(lon, lat, marker='o', color='black', markersize=4, zorder=5, transform=ccrs.PlateCarree())
    ax.text(lon + 0.08, lat + 0.05, name, fontsize=11, fontweight='bold', color='#111111',
            zorder=6, transform=ccrs.PlateCarree(),
            path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=3, foreground='white')])

# 7. Inset Translucent Vertical Legend Bar
cax = fig.add_axes([0.02, 0.10, 0.028, 0.62], facecolor='#111111')
cbar = fig.colorbar(cf, cax=cax, orientation='vertical', ticks=levels)
cbar.set_label('Est. Precipitation (in)', color='white', fontsize=12, fontweight='bold', labelpad=10)
cbar.ax.yaxis.set_tick_params(color='white')
cbar.ax.set_yticklabels(['0.01"', '0.1"', '0.25"', '0.5"', '1"', '1.5"', '2"', '3"', '4"', '6"', '8"'],
                        color='white', fontweight='bold', fontsize=9)

# 8. Top Dark Header Banner
header_ax = fig.add_axes([0.0, 0.92, 1.0, 0.08], facecolor='#09182b')
header_ax.axis('off')

valid_start = yesterday.strftime('%m/%d/%Y 07:00 AM MDT')
valid_end = now.strftime('%m/%d/%Y 07:00 AM MDT')
issued_time = now.strftime('%b %d, %Y %I:%M %p MDT')

header_ax.text(0.02, 0.62, "24-Hour Estimated Rainfall", color='white', fontsize=22, fontweight='bold', va='center')
header_ax.text(0.02, 0.25, f"Valid: {valid_start} - {valid_end}", color='#dcdcdc', fontsize=11, va='center')

header_ax.text(0.98, 0.62, "Weather Forecast Office", color='white', fontsize=11, ha='right', va='center')
header_ax.text(0.98, 0.25, f"Albuquerque, NM | Issued {issued_time}", color='#dcdcdc', fontsize=10, ha='right', va='center')

# 9. Bottom Dark Footer Banner
footer_ax = fig.add_axes([0.0, 0.0, 1.0, 0.04], facecolor='#09182b')
footer_ax.axis('off')
footer_ax.text(0.02, 0.5, "NWSAlbuquerque", color='white', fontsize=11, fontweight='bold', va='center')
footer_ax.text(0.98, 0.5, "weather.gov/abq", color='white', fontsize=11, fontweight='bold', ha='right', va='center')

# Save Clean Output
output_filename = "NM_24h_Rainfall.png"
plt.savefig(output_filename, bbox_inches='tight', pad_inches=0)
print("Map generated and saved successfully!")

da.close()
if os.path.exists(tif_filename):
    os.remove(tif_filename)
