-- MySQL Script generado por MySQL Workbench (esquema apuntando a CommuConnect_1, con CASCADE y correcciones)

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema CommuConnect_1
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `CommuConnect_1`;
CREATE SCHEMA IF NOT EXISTS `CommuConnect_1` DEFAULT CHARACTER SET utf8;
USE `CommuConnect_1`;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`usuario`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`usuario`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`usuario` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(60) NOT NULL,
  `tipo` ENUM('Cliente','Administrador') NULL,
  `apellido` VARCHAR(60) NOT NULL,
  `email` VARCHAR(60) NULL,
  `password` VARCHAR(60) NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`administrador`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`administrador`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`administrador` (
  `id_administrador` INT NOT NULL AUTO_INCREMENT,
  `id_usuario` INT NULL,
  INDEX `id_usuario_idx` (`id_usuario` ASC) VISIBLE,
  PRIMARY KEY (`id_administrador`),
  CONSTRAINT `fk_usuario_adm`
    FOREIGN KEY (`id_usuario`)
    REFERENCES `CommuConnect_1`.`usuario` (`id_usuario`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`departamento`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`departamento`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`departamento` (
  `id_departamento` INT NOT NULL,
  `nombre` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_departamento`)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`distrito`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`distrito`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`distrito` (
  `id_distrito` INT NOT NULL,
  `id_departamento` INT NOT NULL,
  `nombre` VARCHAR(45) NOT NULL,
  `imagen` LONGBLOB NULL,
  PRIMARY KEY (`id_distrito`),
  CONSTRAINT `fk_departamento_dist`
    FOREIGN KEY (`id_departamento`)
    REFERENCES `CommuConnect_1`.`departamento` (`id_departamento`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`cliente`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`cliente`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`cliente` (
  `id_cliente` INT NOT NULL AUTO_INCREMENT,
  `id_usuario` INT NOT NULL,
  `tipo_documento` ENUM('DNI','CARNET DE EXTRANJERIA') NOT NULL,
  `num_doc` VARCHAR(45) NOT NULL,
  `numero_telefono` VARCHAR(45) NOT NULL,
  `id_departamento` INT NOT NULL,
  `id_distrito` INT NOT NULL,
  `direccion` VARCHAR(350) NULL,
  `fecha_nac` DATETIME NULL,
  `genero` VARCHAR(45) NULL,
  `talla` INT NOT NULL,
  `peso` INT NOT NULL,
  PRIMARY KEY (`id_cliente`),
  UNIQUE INDEX `num_doc_UNIQUE` (`num_doc` ASC) VISIBLE,
  INDEX `id_usuario_idx` (`id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_usuario_cli`
    FOREIGN KEY (`id_usuario`)
    REFERENCES `CommuConnect_1`.`usuario` (`id_usuario`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_departamento_cli`
    FOREIGN KEY (`id_departamento`)
    REFERENCES `CommuConnect_1`.`departamento` (`id_departamento`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_distrito_cli`
    FOREIGN KEY (`id_distrito`)
    REFERENCES `CommuConnect_1`.`distrito` (`id_distrito`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`comunidad`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`comunidad`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`comunidad` (
  `id_comunidad` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `slogan` VARCHAR(350) NULL,
  `imagen` LONGBLOB NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_comunidad`)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`servicio`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`servicio`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`servicio` (
  `id_servicio` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `descripccion` VARCHAR(100) NULL,
  `imagen` LONGBLOB NULL,
  `modalidad` ENUM('Virtual','Presencial') NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_servicio`)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`local`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`local`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`local` (
  `id_local` INT NOT NULL AUTO_INCREMENT,
  `id_departamento` INT NOT NULL,
  `id_distrito` INT NOT NULL,
  `direccion_detallada` VARCHAR(350) NULL,
  `id_servicio` INT NULL,
  `responsable` VARCHAR(45) NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_local`),
  INDEX `id_departamento_idx` (`id_departamento` ASC) VISIBLE,
  INDEX `id_distrito_idx` (`id_distrito` ASC) VISIBLE,
  INDEX `id_servicio_idx` (`id_servicio` ASC) VISIBLE,
  CONSTRAINT `fk_departamento_loc`
    FOREIGN KEY (`id_departamento`)
    REFERENCES `CommuConnect_1`.`departamento` (`id_departamento`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_distrito_loc`
    FOREIGN KEY (`id_distrito`)
    REFERENCES `CommuConnect_1`.`distrito` (`id_distrito`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_servicio_loc`
    FOREIGN KEY (`id_servicio`)
    REFERENCES `CommuConnect_1`.`servicio` (`id_servicio`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`comunidadxservicio`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`comunidadxservicio`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`comunidadxservicio` (
  `id_comunidad` INT NOT NULL,
  `id_servicio` INT NOT NULL,
  PRIMARY KEY (`id_comunidad`,`id_servicio`),
  CONSTRAINT `fk_comunidad_CS`
    FOREIGN KEY (`id_comunidad`)
    REFERENCES `CommuConnect_1`.`comunidad` (`id_comunidad`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_servicio_CS`
    FOREIGN KEY (`id_servicio`)
    REFERENCES `CommuConnect_1`.`servicio` (`id_servicio`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`clientexcomunidad`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`clientexcomunidad`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`clientexcomunidad` (
  `id_cliente` INT NOT NULL,
  `id_comunidad` INT NOT NULL,
  PRIMARY KEY (`id_cliente`,`id_comunidad`),
  CONSTRAINT `fk_cliente_CC`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `CommuConnect_1`.`cliente` (`id_cliente`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_comunidad_CC`
    FOREIGN KEY (`id_comunidad`)
    REFERENCES `CommuConnect_1`.`comunidad` (`id_comunidad`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`sesion`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`sesion`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`sesion` (
  `id_sesion` INT NOT NULL AUTO_INCREMENT,
  `id_servicio` INT NULL,
  `tipo` ENUM('Virtual','Presencial') NULL,
  `descripcion` VARCHAR(100) NOT NULL,
  `inicio` DATETIME NULL,
  `fin` DATETIME NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_sesion`),
  INDEX `id_servicio_idx` (`id_servicio` ASC) VISIBLE,
  CONSTRAINT `fk_servicio_ses`
    FOREIGN KEY (`id_servicio`)
    REFERENCES `CommuConnect_1`.`servicio` (`id_servicio`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`sesion_presencial`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`sesion_presencial`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`sesion_presencial` (
  `id_sesion_presencial` INT NOT NULL AUTO_INCREMENT,
  `id_sesion` INT NULL,
  `id_local` INT NULL,
  `capacidad` INT NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_sesion_presencial`),
  CONSTRAINT `fk_sesion_SP`
    FOREIGN KEY (`id_sesion`)
    REFERENCES `CommuConnect_1`.`sesion` (`id_sesion`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_local_SP`
    FOREIGN KEY (`id_local`)
    REFERENCES `CommuConnect_1`.`local` (`id_local`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`profesional`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`profesional`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`profesional` (
  `id_profesional` INT NOT NULL AUTO_INCREMENT,
  `id_usuario` INT NULL,
  `formulario` BLOB NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_profesional`),
  INDEX `id_usuario_idx` (`id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_usuario_PRO`
    FOREIGN KEY (`id_usuario`)
    REFERENCES `CommuConnect_1`.`usuario` (`id_usuario`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`sesion_virtual`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`sesion_virtual`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`sesion_virtual` (
  `id_sesion_virtual` INT NOT NULL AUTO_INCREMENT,
  `id_sesion` INT NULL,
  `id_profesional` INT NULL,
  `doc_asociado` BLOB NULL,
  `url_meeting` VARCHAR(500) NULL,
  `url_archivo` VARCHAR(500) NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_sesion_virtual`),
  CONSTRAINT `fk_sesion_SV`
    FOREIGN KEY (`id_sesion`)
    REFERENCES `CommuConnect_1`.`sesion` (`id_sesion`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_profesional_SV`
    FOREIGN KEY (`id_profesional`)
    REFERENCES `CommuConnect_1`.`profesional` (`id_profesional`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`reserva`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`reserva`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`reserva` (
  `id_reserva` INT NOT NULL AUTO_INCREMENT,
  `id_sesion` INT NULL,
  `id_cliente` INT NULL,
  `fecha_reservada` DATETIME NULL,
  `estado_reserva` VARCHAR(45) NULL,
  `archivo` LONGBLOB NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_reserva`),
  CONSTRAINT `fk_sesion_R`
    FOREIGN KEY (`id_sesion`)
    REFERENCES `CommuConnect_1`.`sesion` (`id_sesion`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_cliente_R`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `CommuConnect_1`.`cliente` (`id_cliente`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`plan`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`plan`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`plan` (
  `id_plan` INT NOT NULL AUTO_INCREMENT,
  `titulo` VARCHAR(100) NULL,
  `descripcion` VARCHAR(300) NULL,
  `topes` INT NULL,
  `precio` DECIMAL(10,2) NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_plan`)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`pago`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`pago`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`pago` (
  `id_pago` INT NOT NULL AUTO_INCREMENT,
  `monto` DECIMAL(10,2) NULL,
  `fecha_pago` DATETIME NULL,
  `metodo_pago` ENUM('Tarjeta','Otro') NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_pago`)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`inscripcion`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`inscripcion`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`inscripcion` (
  `id_inscripcion` INT NOT NULL AUTO_INCREMENT,
  `id_plan` INT NULL,
  `id_comunidad` INT NULL,
  `id_cliente` INT NULL,
  `id_pago` INT NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_inscripcion`),
  CONSTRAINT `fk_plan_ins`
    FOREIGN KEY (`id_plan`)
    REFERENCES `CommuConnect_1`.`plan` (`id_plan`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_comunidad_ins`
    FOREIGN KEY (`id_comunidad`)
    REFERENCES `CommuConnect_1`.`comunidad` (`id_comunidad`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_cliente_ins`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `CommuConnect_1`.`cliente` (`id_cliente`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_pago_ins`
    FOREIGN KEY (`id_pago`)
    REFERENCES `CommuConnect_1`.`pago` (`id_pago`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`detalle_inscripcion`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`detalle_inscripcion`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`detalle_inscripcion` (
  `id_registros_inscipcion` INT NOT NULL AUTO_INCREMENT,
  `id_inscripcion` INT NULL,
  `fecha_registro` DATETIME NULL,
  `fecha_inicio` DATETIME NULL,
  `fecha_fin` DATETIME NULL,
  `topes_disponibles` INT NULL,
  `topes_consumidos` INT NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_registros_inscipcion`),
  CONSTRAINT `fk_inscripcion_DI`
    FOREIGN KEY (`id_inscripcion`)
    REFERENCES `CommuConnect_1`.`inscripcion` (`id_inscripcion`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table `CommuConnect_1`.`suspension`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `CommuConnect_1`.`suspension`;
CREATE TABLE IF NOT EXISTS `CommuConnect_1`.`suspension` (
  `id_suspension` INT NOT NULL AUTO_INCREMENT,
  `id_cliente` INT NULL,
  `id_inscripcion` INT NULL,
  `motivo` VARCHAR(300) NULL,
  `fecha_inicio` DATETIME NULL,
  `fecha_fin` DATETIME NULL,
  `archivo` LONGBLOB NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_suspension`),
  CONSTRAINT `fk_cliente_sus`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `CommuConnect_1`.`cliente` (`id_cliente`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_inscripcion_sus`
    FOREIGN KEY (`id_inscripcion`)
    REFERENCES `CommuConnect_1`.`inscripcion` (`id_inscripcion`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
