/*CREATE DATABASE BiometricosDBRC;
USE BiometricosDBRC;
*/
CREATE TABLE biometricos (
    id_biometrico INT(3) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(20) NOT NULL,
    sn VARCHAR(50) NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    estado BOOLEAN NOT NULL,
    usuario VARCHAR(30),
    contrasena VARCHAR(30) NOT NULL,
    ubicacion VARCHAR(100),
    ultima_sincronizacion DATETIME
);

CREATE TABLE empleados (
    id_empleado INT(3) UNSIGNED NOT NULL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    departamento VARCHAR(100),
    turno VARCHAR(50),
    estado BOOLEAN NOT NULL,
    mail VARCHAR(100)
);

CREATE TABLE registros (
    id_registro INT(100) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    register_time DATETIME NOT NULL,
    tipo_registro VARCHAR(50),
    id_biometrico INT(3) UNSIGNED NOT NULL,
    id_empleado INT(3) UNSIGNED NOT NULL,
    FOREIGN KEY(id_biometrico) REFERENCES biometricos(id_biometrico),
    FOREIGN KEY(id_empleado) REFERENCES empleados(id_empleado)
);
