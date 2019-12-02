/*
Karl Osen
"Accurate Conversion of Earth Fixed Earth Centered Coordinates to Geodetic Coordinates",
2019-10-31
*/

#include <math.h>
#include "wgs84.h"
const static double invcbrt2 = WGS84_INVCBRT2; // 1/(2^(1/3))
const static double inv3 = WGS84_INV3; // 1/3
const static double inv6 = WGS84_INV6; // 1/6
/*****************************************************************************\
|* Convert geodetic coordinates to ECEF coordinates
\*****************************************************************************/

double radians(double deg) {
    return deg / 180.0 * M_PI;
}

double degrees(double rad) {
    return rad / M_PI * 180.0;
}

ECEF wgs84_to_ecef(double lat, double lon, double alt) {
    double N;
    double coslon, sinlon;
    double coslat, sinlat;
    double d;
    ECEF ecef;
    coslat = cos(lat);
    sinlat = sin(lat);
    coslon = cos(lon);
    sinlon = sin(lon);
    N = WGS84_AADC / sqrt(coslat * coslat + WGS84_BBDCC);
    d = (N + alt) * coslat;
    ecef.x = d * coslon;
    ecef.y = d * sinlon;
    ecef.z = (WGS84_P1MEE * N + alt) * sinlat;
    return ecef;
}

ECEF geodetic_to_ecef(double lat, double lon, double alt) {
    ECEF ecef;
    double coslat = cos(lat);
    ecef.x = coslat * cos(lon) * alt;
    ecef.y = coslat * sin(lon) * alt;
    ecef.z = sin(lat) * alt;
    return ecef;
}

ECEF spherical_to_ecef(double lat, double lon, double alt) {
    ECEF ecef;
    double coslat = cos(lat);
    ecef.x = coslat * cos(lon);
    ecef.y = coslat * sin(lon);
    ecef.z = sin(lat);
    return ecef;
}

WGS84 ecef_to_geodetic(double x, double y, double z) {
    WGS84 geo;
    double r = sqrt(x * x + y * y + z * z);
    geo.lat = degrees(asin(z / r));
    geo.lon = fmod(degrees(atan2(y, x)), 360);
    geo.alt = r - 6371000;
    return geo;
}

WGS84 ecef_to_spherical(double x, double y, double z) {
    WGS84 geo;
    double r = sqrt(x * x + y * y + z * z);
    geo.lat = degrees(asin(z / r));
    geo.lon = fmod(degrees(atan2(y, x)), 360);
    geo.alt = r;
    return geo;
}

WGS84 ecef_to_wgs84(double x, double y, double z) {
    // The variables below correspond to symbols used in the paper
    // "Accurate Conversion of Earth-Centered, Earth-Fixed Coordinates
    // to Geodetic Coordinates"
    double beta;
    double C;
    double dw;
    double dz;
    double F, G, H, i, k, m, n, p, P;
    double t;
    double u;
    double v;
    double w;
    // Intermediate variables
    double r_squared; // w^2
    double mpn; // m+n
    double g;
    double tt; // t^2
    double ttt; // t^3
    double tttt; // t^4
    double zu; // z * u
    double wv; // w * v
    double invuv; // 1 / (u * v)
    double da;
    double t4, t5, t6, t7;
    WGS84 geo;
    r_squared = x * x + y * y;
    m = r_squared * WGS84_INVAA;
    n = z * z * WGS84_P1MEEDAA;
    mpn = m + n;
    p = inv6 * (mpn - WGS84_EEEE);
    G = m * n * WGS84_EEEED4;
    H = 2 * p * p * p + G;
    
    if (H < WGS84_HMIN) {
       return geo;
    }
   
    C = pow(H + G + 2 * sqrt(H * G), inv3) * invcbrt2;
    i = -WGS84_EEEED4 - 0.5 * mpn;
    P = p * p;
    beta = inv3 * i - C - P / C;
    k = WGS84_EEEED4 * (WGS84_EEEED4 - mpn);
    // Compute left part of t
    t4 = sqrt(sqrt(beta * beta - k) - 0.5 * (beta + i));
    // Compute right part of t
    t5 = fabs(0.5 * (beta - i));
    // t5 may accidentally drop just below zero due to numeric turbulence
    // This only occurs at latitudes close to +- 45.3 degrees
    t6 = sqrt(t5);
    t7 = (m < n) ? t6 : -t6;
    // Add left and right parts
    t = t4 + t7;
    // Use Newton-Raphson's method to compute t correction
    g = 2 * WGS84_EED2 * (m - n);
    tt = t * t;
    ttt = tt * t;
    tttt = tt * tt;
    F = tttt + 2 * i * tt + g * t + k;
    t += -F / (4 * ttt + 4 * i * t + g);
    // compute latitude (range -PI/2..PI/2)
    u = t + WGS84_EED2;
    v = t - WGS84_EED2;
    w = sqrt(r_squared);
    zu = z * u;
    wv = w * v;
    // compute altitude
    invuv = 1 / (u * v);
    dw = w - wv * invuv;
    dz = z - zu * WGS84_P1MEE * invuv;
    da = sqrt(dw * dw + dz * dz);
    // compute longitude (range -PI..PI)
    geo.lon = degrees(atan2(y, x));
    geo.lat = degrees(atan2(zu, wv));
    geo.alt = (u < 1) ? -da : da;
    return geo;
}
