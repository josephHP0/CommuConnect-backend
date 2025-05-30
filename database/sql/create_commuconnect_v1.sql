-- MySQL Script generated by MySQL Workbench
-- Tue May 13 13:55:44 2025
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema commuconnect
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `commuconnect` ;

-- -----------------------------------------------------
-- Schema commuconnect
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `commuconnect` DEFAULT CHARACTER SET utf8 ;
USE `commuconnect` ;

-- -----------------------------------------------------
-- Table `commuconnect`.`usuario`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`usuario` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`usuario` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(60) NOT NULL,
  `apellido` VARCHAR(60) NOT NULL,
  `email` VARCHAR(60) NULL,
  `password` VARCHAR(60) NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `commuconnect`.`administrador`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`administrador` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`administrador` (
  `id_administrador` INT NOT NULL AUTO_INCREMENT,
  `id_usuario` INT NULL,
  INDEX `id_usuario_idx` (`id_usuario` ASC) VISIBLE,
  PRIMARY KEY (`id_administrador`),
  CONSTRAINT `fk_usuario`
    FOREIGN KEY (`id_usuario`)
    REFERENCES `commuconnect`.`usuario` (`id_usuario`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `commuconnect`.`ciudad`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`ciudad` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`ciudad` (
  `id_ciudad` INT NOT NULL,
  `nombre` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_ciudad`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `commuconnect`.`distrito`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`distrito` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`distrito` (
  `id_distrito` INT NOT NULL,
  `nombre` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_distrito`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `commuconnect`.`direccion`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`direccion` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`direccion` (
  `id_direccion` INT NOT NULL AUTO_INCREMENT,
  `id_ciudad` INT NULL,
  `id_distrito` INT NULL,
  PRIMARY KEY (`id_direccion`),
  INDEX `id_ciudad_idx` (`id_ciudad` ASC) VISIBLE,
  INDEX `id_distrito_idx` (`id_distrito` ASC) VISIBLE,
  CONSTRAINT `id_ciudad`
    FOREIGN KEY (`id_ciudad`)
    REFERENCES `commuconnect`.`ciudad` (`id_ciudad`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `id_distrito`
    FOREIGN KEY (`id_distrito`)
    REFERENCES `commuconnect`.`distrito` (`id_distrito`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `commuconnect`.`cliente`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`cliente` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`cliente` (
  `id_cliente` INT NOT NULL AUTO_INCREMENT,
  `id_usuario` INT NOT NULL,
  `id_direccion` INT NOT NULL,
  `tipo_documento` ENUM('DNI', 'CARNET DE EXTRANJERIA') NOT NULL,
  `num_doc` VARCHAR(45) NOT NULL,
  `direccion_detallada` VARCHAR(350) NULL,
  `fecha_nac` DATETIME NULL,
  `genero` VARCHAR(45) NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_cliente`),
  UNIQUE INDEX `num_doc_UNIQUE` (`num_doc` ASC) VISIBLE,
  INDEX `id_usuario_idx` (`id_usuario` ASC) VISIBLE,
  INDEX `id_direccion_idx` (`id_direccion` ASC) VISIBLE,
  CONSTRAINT `fk_usuario_cli`
    FOREIGN KEY (`id_usuario`)
    REFERENCES `commuconnect`.`usuario` (`id_usuario`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_direccion_cli`
    FOREIGN KEY (`id_direccion`)
    REFERENCES `commuconnect`.`direccion` (`id_direccion`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `commuconnect`.`Tipo_Documento`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`Tipo_Documento` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`Tipo_Documento` (
  `id_tipo_documento` INT NOT NULL,
  `nombre` VARCHAR(45) NULL,
  `abreviatura` VARCHAR(45) NULL,
  PRIMARY KEY (`id_tipo_documento`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `commuconnect`.`comunidad`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`comunidad` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`comunidad` (
  `id_comunidad` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `slogan` VARCHAR(350) NULL,
  `imagen` LONGBLOB NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_comunidad`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `commuconnect`.`servicio`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`servicio` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`servicio` (
  `id_servicio` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `descripccion` VARCHAR(100) NULL,
  `imagen` LONGBLOB NULL,
  `modalidad` ENUM('Virtual', 'Presencial') NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_servicio`));


-- -----------------------------------------------------
-- Table `commuconnect`.`local`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`local` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`local` (
  `id_local` INT NOT NULL AUTO_INCREMENT,
  `id_direccion` INT NULL,
  `id_servicio` INT NULL,
  `direccion_detallada` VARCHAR(350) NULL,
  `responsable` VARCHAR(45) NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_local`),
  INDEX `id_servicio_idx` (`id_servicio` ASC) VISIBLE,
  INDEX `id_direccion_idx` (`id_direccion` ASC) VISIBLE,
  CONSTRAINT `fk_servicio_l`
    FOREIGN KEY (`id_servicio`)
    REFERENCES `commuconnect`.`servicio` (`id_servicio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_direccion_l`
    FOREIGN KEY (`id_direccion`)
    REFERENCES `commuconnect`.`direccion` (`id_direccion`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);


-- -----------------------------------------------------
-- Table `commuconnect`.`comunidadxservicio`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`comunidadxservicio` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`comunidadxservicio` (
  `id_comunidad` INT NOT NULL,
  `id_servicio` INT NOT NULL,
  PRIMARY KEY (`id_comunidad`, `id_servicio`),
  INDEX `id_servicio_idx` (`id_servicio` ASC) VISIBLE,
  CONSTRAINT `fk_comunidad_CS`
    FOREIGN KEY (`id_comunidad`)
    REFERENCES `commuconnect`.`comunidad` (`id_comunidad`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_servicio_CS`
    FOREIGN KEY (`id_servicio`)
    REFERENCES `commuconnect`.`servicio` (`id_servicio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `commuconnect`.`clientexcomunidad`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`clientexcomunidad` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`clientexcomunidad` (
  `id_cliente` INT NOT NULL,
  `id_comunidad` INT NOT NULL,
  PRIMARY KEY (`id_cliente`, `id_comunidad`),
  INDEX `id_comunidad_idx` (`id_comunidad` ASC) VISIBLE,
  CONSTRAINT `fk_cliente_CC`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `commuconnect`.`cliente` (`id_cliente`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_comunidad_CC`
    FOREIGN KEY (`id_comunidad`)
    REFERENCES `commuconnect`.`comunidad` (`id_comunidad`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `commuconnect`.`sesion`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`sesion` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`sesion` (
  `id_sesion` INT NOT NULL AUTO_INCREMENT,
  `id_servicio` INT NULL,
  `descripccion` VARCHAR(100) NOT NULL,
  `inicio` DATETIME NULL,
  `fin` DATETIME NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_sesion`),
  INDEX `id_servicio_idx` (`id_servicio` ASC) VISIBLE,
  CONSTRAINT `fk_servicio_S`
    FOREIGN KEY (`id_servicio`)
    REFERENCES `commuconnect`.`servicio` (`id_servicio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);


-- -----------------------------------------------------
-- Table `commuconnect`.`sesion_presencial`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`sesion_presencial` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`sesion_presencial` (
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
  INDEX `id_sesion_idx` (`id_sesion` ASC) VISIBLE,
  INDEX `id_local_idx` (`id_local` ASC) VISIBLE,
  CONSTRAINT `fk_sesion_SP`
    FOREIGN KEY (`id_sesion`)
    REFERENCES `commuconnect`.`sesion` (`id_sesion`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_local_SP`
    FOREIGN KEY (`id_local`)
    REFERENCES `commuconnect`.`local` (`id_local`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);


-- -----------------------------------------------------
-- Table `commuconnect`.`profesional`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`profesional` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`profesional` (
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
    REFERENCES `commuconnect`.`usuario` (`id_usuario`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);


-- -----------------------------------------------------
-- Table `commuconnect`.`sesion_virtual`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`sesion_virtual` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`sesion_virtual` (
  `id_sesion_virtual` INT NOT NULL AUTO_INCREMENT,
  `id_sesion` INT NULL,
  `id_profesional` INT NULL,
  `doc_asociado` BLOB NULL,
  `descripcion?` VARCHAR(300) NULL,
  `URL` VARCHAR(500) NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_sesion_virtual`),
  INDEX `id_sesion_idx` (`id_sesion` ASC) VISIBLE,
  INDEX `id_profesional_idx` (`id_profesional` ASC) VISIBLE,
  CONSTRAINT `fk_sesion_SV`
    FOREIGN KEY (`id_sesion`)
    REFERENCES `commuconnect`.`sesion` (`id_sesion`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_profesional_SV`
    FOREIGN KEY (`id_profesional`)
    REFERENCES `commuconnect`.`profesional` (`id_profesional`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);


-- -----------------------------------------------------
-- Table `commuconnect`.`reserva`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`reserva` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`reserva` (
  `id_reserva` INT NOT NULL AUTO_INCREMENT,
  `id_sesion` INT NULL,
  `id_cliente` INT NULL,
  `fecha_reservada` DATETIME NULL,
  `estado_reserva` VARCHAR(45) NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_reserva`),
  INDEX `id_cliente_idx` (`id_cliente` ASC) VISIBLE,
  INDEX `id_sesion_idx` (`id_sesion` ASC) VISIBLE,
  CONSTRAINT `fk_sesion_R`
    FOREIGN KEY (`id_sesion`)
    REFERENCES `commuconnect`.`sesion` (`id_sesion`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_cliente_R`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `commuconnect`.`cliente` (`id_cliente`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);


-- -----------------------------------------------------
-- Table `commuconnect`.`plan`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`plan` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`plan` (
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
  PRIMARY KEY (`id_plan`));


-- -----------------------------------------------------
-- Table `commuconnect`.`pago`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`pago` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`pago` (
  `id_pago` INT NOT NULL AUTO_INCREMENT,
  `monto` DECIMAL(10,2) NULL,
  `fecha_pago` DATETIME NULL,
  `metodo_pago` ENUM('Tarjeta', 'Efectivo') NULL,
  `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_por` VARCHAR(50) NULL,
  `fecha_modificacion` TIMESTAMP NULL,
  `modificado_por` VARCHAR(50) NULL,
  `estado` TINYINT NULL,
  PRIMARY KEY (`id_pago`));


-- -----------------------------------------------------
-- Table `commuconnect`.`inscripcion`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`inscripcion` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`inscripcion` (
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
  INDEX `id_comunidad_idx` (`id_comunidad` ASC) VISIBLE,
  INDEX `id_cliente_idx` (`id_cliente` ASC) VISIBLE,
  INDEX `id_plan_idx` (`id_plan` ASC) VISIBLE,
  INDEX `id_pago_idx` (`id_pago` ASC) VISIBLE,
  CONSTRAINT `fk_comunidad_I`
    FOREIGN KEY (`id_comunidad`)
    REFERENCES `commuconnect`.`comunidad` (`id_comunidad`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_cliente_I`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `commuconnect`.`cliente` (`id_cliente`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_plan_I`
    FOREIGN KEY (`id_plan`)
    REFERENCES `commuconnect`.`plan` (`id_plan`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_pago_I`
    FOREIGN KEY (`id_pago`)
    REFERENCES `commuconnect`.`pago` (`id_pago`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);


-- -----------------------------------------------------
-- Table `commuconnect`.`detalle_inscripcion`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`detalle_inscripcion` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`detalle_inscripcion` (
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
  INDEX `id_inscripcion_idx` (`id_inscripcion` ASC) VISIBLE,
  CONSTRAINT `fk_inscripcion_DI`
    FOREIGN KEY (`id_inscripcion`)
    REFERENCES `commuconnect`.`inscripcion` (`id_inscripcion`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);


-- -----------------------------------------------------
-- Table `commuconnect`.`suspension`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `commuconnect`.`suspension` ;

CREATE TABLE IF NOT EXISTS `commuconnect`.`suspension` (
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
  INDEX `id_cliente_idx` (`id_cliente` ASC) VISIBLE,
  INDEX `id_inscripcion_idx` (`id_inscripcion` ASC) VISIBLE,
  CONSTRAINT `fk_cliente_Sus`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `commuconnect`.`cliente` (`id_cliente`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_inscripcion_Sus`
    FOREIGN KEY (`id_inscripcion`)
    REFERENCES `commuconnect`.`inscripcion` (`id_inscripcion`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
