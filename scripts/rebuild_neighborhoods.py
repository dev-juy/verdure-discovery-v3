import json
from pathlib import Path
from urllib.parse import urlencode
root=Path(__file__).resolve().parents[1]
oed=json.loads((root/'data/geo_provenance/oed.json').read_text())
opn=json.loads((root/'data/geo_provenance/sj.json').read_text())
cities=json.loads((root/'data/geo_provenance/cities.json').read_text())
def inside(x,y,ring):
 yes=False
 for (x1,y1),(x2,y2) in zip(ring,ring[1:]):
  if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:yes=not yes
 return yes

def point(geometry):
 rings=geometry['coordinates'] if geometry['type']=='Polygon' else max(geometry['coordinates'],key=lambda p:len(p[0]))
 ring=rings[0]
 ys=[p[1] for p in ring];y=(min(ys)+max(ys))/2
 xs=[]
 for (x1,y1),(x2,y2) in zip(ring,ring[1:]):
  if (y1>y)!=(y2>y):xs.append(x1+(y-y1)*(x2-x1)/(y2-y1))
 xs.sort();l,r=max(zip(xs[::2],xs[1::2]),key=lambda lr:lr[1]-lr[0]);x=(l+r)/2
 assert inside(x,y,ring)
 assert not any(inside(x,y,hole) for hole in rings[1:])
 return y,x
areas=[]
for label,fieldname,dataset,official,layer in [
 ('downtown san jose','NEIGHBORHOODNAME',oed,'Downtown','OED/OED_AllReferenceLayers/MapServer/3'),
 ('willow glen','NEIGHBORHOODNAME',oed,'Willow Glen','OED/OED_AllReferenceLayers/MapServer/3'),
 ('almaden','NEIGHBORHOODNAME',oed,'Almaden Valley','OED/OED_AllReferenceLayers/MapServer/3'),
 ('evergreen','NEIGHBORHOODNAME',oed,'Evergreen','OED/OED_AllReferenceLayers/MapServer/3'),
 ('cambrian','NAME',opn,'Cambrian','OPN/OPN_OpenDataService/MapServer/549')]:
 feature=next(f for f in dataset['features'] if f['properties'][fieldname]==official);lat,lon=point(feature['geometry'])
 url='https://geo.sanjoseca.gov/server/rest/services/'+layer+'/query?'+urlencode({'f':'geojson','where':fieldname+"='"+official+"'",'outFields':'*','outSR':4326})
 areas.append(dict(name=label,latitude=lat,longitude=lon,source=url,official_name=official,source_objectid=feature['properties']['OBJECTID'],checked_on='2026-11-08',confirmed_live=True,note='Interior point computed from the official WGS84 polygon: midpoint of its widest horizontal intersection at the outer ring mid-latitude; not a neighborhood centroid.'))
for f in cities['features']:
 a=f['attributes'];areas.append(dict(name=a['BASENAME'].lower(),latitude=float(a['INTPTLAT']),longitude=float(a['INTPTLON']),source='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/4/query?'+urlencode({'f':'json','where':"GEOID='"+a['GEOID']+"'",'outFields':'BASENAME,GEOID,INTPTLAT,INTPTLON','returnGeometry':'false'}),official_name=a['NAME'],geoid=a['GEOID'],checked_on='2026-11-08',confirmed_live=True,note='U.S. Census TIGERweb incorporated-place internal point; city, not neighborhood.'))
areas.append(dict(name='sjsu',latitude=37.335187,longitude=-121.881072,source='https://events.sjsu.edu/event/global-connections-diy-diyas',anchor='SJSU Student Union, One Washington Square, San Jose, CA 95192',checked_on='2026-11-08',confirmed_live=True,note='Campus anchor from official university page structured coordinates; SJSU is not a neighborhood.'))
(root/'data/neighborhoods.json').write_text(json.dumps({'_note':'Official City of San Jose GIS neighborhood polygons and Census city internal points. Coordinates derived on 2026-11-08. Campus exception explicitly labeled. Snapshot data and derivation are in data/geo_provenance.','areas':areas},indent=2)+'\n')
print('Wrote', len(areas), 'official area points')
