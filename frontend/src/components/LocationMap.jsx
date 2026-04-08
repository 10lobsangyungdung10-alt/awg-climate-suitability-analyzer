/**
 * LocationMap component
 * Renders an interactive Leaflet map centred on the analyzed location.
 *
 * IMPORTANT: Leaflet's default marker icons break when bundled with Vite because
 * Vite rewrites asset paths. We fix this by manually supplying the icon URLs.
 */
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Fix default marker icon paths broken by Vite's asset hashing
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

/**
 * @param {object} props
 * @param {number} props.latitude     - Decimal latitude
 * @param {number} props.longitude    - Decimal longitude
 * @param {string} props.locationName - Display name shown in the popup
 */
export default function LocationMap({ latitude, longitude, locationName }) {
  // Guard against missing coordinates
  if (latitude === undefined || latitude === null ||
      longitude === undefined || longitude === null) {
    return null;
  }

  const lat = Number(latitude);
  const lon = Number(longitude);
  const name = locationName || 'Selected Location';

  return (
    <div className="card map-card">
      <h2 className="map-title">
        <span aria-hidden="true">🗺️</span> Location Map
      </h2>

      {/* MapContainer must have an explicit height */}
      <div className="map-container">
        <MapContainer
          center={[lat, lon]}
          zoom={10}
          scrollWheelZoom={false}
          style={{ height: '100%', width: '100%', borderRadius: '8px' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={[lat, lon]}>
            <Popup>
              <strong>{name}</strong>
              <br />
              {lat.toFixed(4)}°, {lon.toFixed(4)}°
            </Popup>
          </Marker>
        </MapContainer>
      </div>
    </div>
  );
}
