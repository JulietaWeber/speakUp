const express = require("express");
const router = express.Router();

const {
  obtenerPictogramas,
  obtenerPictogramasPorCategoria,
  crearPictograma,
  actualizarPictograma,
  eliminarPictograma,
  crearPictogramaPersonalizado,
  obtenerMisPictogramasPersonalizados,
  actualizarPictogramaPersonalizado,
  eliminarPictogramaPersonalizado,
  crearPictogramaPersonalizadoConImagen,
  actualizarImagenPictogramaPersonalizado,
  crearPictogramaConImagen,
  actualizarImagenPictogramaGeneral
} = require("../controllers/pictogramas.controller");

const verificarToken = require("../middlewares/auth.middleware");
const verificarAdmin = require("../middlewares/admin.middleware");
const upload = require("../middlewares/upload.middleware");

// Públicas
router.get("/", obtenerPictogramas);

router.get("/categoria/:id_categoria", obtenerPictogramasPorCategoria);

// Personalizados del usuario
router.post("/personalizado", verificarToken, crearPictogramaPersonalizado);

router.post(
  "/personalizado-con-imagen",
  verificarToken,
  upload.single("imagen"),
  crearPictogramaPersonalizadoConImagen
);

router.get(
  "/mis-personalizados",
  verificarToken,
  obtenerMisPictogramasPersonalizados
);

router.put(
  "/personalizado/:id_pictograma/imagen",
  verificarToken,
  upload.single("imagen"),
  actualizarImagenPictogramaPersonalizado
);

router.put(
  "/personalizado/:id_pictograma",
  verificarToken,
  actualizarPictogramaPersonalizado
);

router.delete(
  "/personalizado/:id_pictograma",
  verificarToken,
  eliminarPictogramaPersonalizado
);

// Generales / default, solo admin
router.post(
  "/con-imagen",
  verificarToken,
  verificarAdmin,
  upload.single("imagen"),
  crearPictogramaConImagen
);

router.post(
  "/",
  verificarToken,
  verificarAdmin,
  crearPictograma
);

router.put(
  "/:id_pictograma/imagen",
  verificarToken,
  verificarAdmin,
  upload.single("imagen"),
  actualizarImagenPictogramaGeneral
);

router.put(
  "/:id_pictograma",
  verificarToken,
  verificarAdmin,
  actualizarPictograma
);

router.delete(
  "/:id_pictograma",
  verificarToken,
  verificarAdmin,
  eliminarPictograma
);

module.exports = router;