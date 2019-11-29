/*
Karl Osen
"Accurate Conversion of Earth Fixed Earth Centered Coordinates to Geodetic Coordinates",
2019-10-31
*/

#include <math.h>
#include "wgs84def.h"
#include "wgs84data.h"
#include "wgs84.h"
const static double invaa = WGS84_INVAA; // 1/(a^2)
const static double aadc = WGS84_AADC; // (a^2)/c
const static double bbdcc = WGS84_BBDCC; // (b^2)/(c^2)
const static double l = WGS84_EED2; // (e^2)/2
const static double p1mee = WGS84_P1MEE; // 1-(e^2)
const static double p1meedaa = WGS84_P1MEEDAA; // (1-(e^2))/(a^2)
const static double Hmin = WGS84_HMIN; // (e^12)/4
const static double ll4 = WGS84_EEEE; // 4*(l^2) = e^4
const static double ll = WGS84_EEEED4; // l^2 = (e^4)/4
const static double invcbrt2 = WGS84_INVCBRT2; // 1/(2^(1/3))
const static double inv3 = WGS84_INV3; // 1/3
const static double inv6 = WGS84_INV6; // 1/6
const static double d2r = WGS84_D2R; // PI/180
const static double r2d = WGS84_R2D; // 180/PI
/*****************************************************************************\
|* Convert geodetic coordinates to ECEF coordinates
\*****************************************************************************/
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
    N = aadc / sqrt(coslat * coslat + bbdcc);
    d = (N + alt) * coslat;
    ecef.x = d * coslon;
    ecef.y = d * sinlon;
    ecef.z = (p1mee * N + alt) * sinlat;
    return ecef;
}
/*****************************************************************************\
|* Convert ECEF coordinates to geodetic coordinates
\*****************************************************************************/
WGS84 ecef_to_wgs84(double x, double y, double z) {
 double lat, lon, alt;
 // The variables below correspond to symbols used in the paper
 // "Accurate Conversion of Earth-Centered, Earth-Fixed Coordinates
 // to Geodetic Coordinates"
 double beta;
 double C;
 double dFdt;
 double dt;
 double dw;
 double dz;
 double F;
 double G;
 double H;
 double i;
 double k;
 double m;
 double n;
 double p;
 double P;
 double t;
 double u;
 double v;
 double w;
 // Intermediate variables
 double j;
 double ww; // w^2
 double mpn; // m+n
 double g;
 double tt; // t^2
 double ttt; // t^3
 double tttt; // t^4
 double zu; // z * u
 double wv; // w * v
 double invuv; // 1 / (u * v)
 double da;
 double t1, t2, t3, t4, t5, t6, t7;
 WGS84 geo;
 ww = x * x + y * y;
 m = ww * invaa;
 n = z * z * p1meedaa;
 mpn = m + n;
 p = inv6 * (mpn - ll4);
 G = m * n * ll;
 H = 2 * p * p * p + G;
 
 if (H < Hmin) {
    return geo;
 }

 C = pow(H + G + 2 * sqrt(H * G), inv3) * invcbrt2;
 i = -ll - 0.5 * mpn;
 P = p * p;
 beta = inv3 * i - C - P / C;
 k = ll * (ll - mpn);
 // Compute left part of t
 t1 = beta * beta - k;
 t2 = sqrt(t1);
 t3 = t2 - 0.5 * (beta + i);
 t4 = sqrt(t3);
 // Compute right part of t
 t5 = 0.5 * (beta - i);
 // t5 may accidentally drop just below zero due to numeric turbulence
 // This only occurs at latitudes close to +- 45.3 degrees
 t5 = fabs(t5);
 t6 = sqrt(t5);
 t7 = (m < n) ? t6 : -t6;
 // Add left and right parts
 t = t4 + t7;
 // Use Newton-Raphson's method to compute t correction
 j = l * (m - n);
 g = 2 * j;
 tt = t * t;
 ttt = tt * t;
 tttt = tt * tt;
 F = tttt + 2 * i * tt + g * t + k;
 dFdt = 4 * ttt + 4 * i * t + g;
 dt = -F / dFdt;
 // compute latitude (range -PI/2..PI/2)
 u = t + dt + l;
 v = t + dt - l;
 w = sqrt(ww);
 zu = z * u;
 wv = w * v;
 lat = atan2(zu, wv);
 // compute altitude
 invuv = 1 / (u * v);
 dw = w - wv * invuv;
 dz = z - zu * p1mee * invuv;
 da = sqrt(dw * dw + dz * dz);
 alt = (u < 1) ? -da : da;
 // compute longitude (range -PI..PI)
 lon = atan2(y, x);
 geo.lat = lat;
 geo.lon = lon;
 geo.alt = alt;
 return geo;
}
