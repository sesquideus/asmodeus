class Geographic {
private:
    double latitude, longitude, altitude;
}


class Spherical {
private:
    double altitude, azimuth, distance;
}


class EarthLocation {
private:
    double x, y, z;
public:
    ECEF(double x, double y, double z);
    ECEF operator+(const Vector& diff);
    ECEF operator-(const Vector& diff);
    Geographic as_spherical(void) const;
    Geographic as_WGS84(void) const;
}
