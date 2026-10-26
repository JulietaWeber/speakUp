
const express = require("express");
const router = express.Router();

const verificarToken = require("../middlewares/auth.middleware");
const verificarTokenOpcional = require("../middlewares/authOpcional.middleware");
const verificarAdmin = require("../middlewares/admin.middleware");
const upload = require("../middlewares/upload.middleware");

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

// =====================================
// CONSULTAS PÚBLICAS / TOKEN OPCIONAL
// =====================================

router.get(
  "/",
  verificarTokenOpcional,
  obtenerPictogramas
);

router.get(
  "/categoria/:id_categoria",
  verificarTokenOpcional,
  obtenerPictogramasPorCategoria
);

// =====================================
// PICTOGRAMAS PERSONALIZADOS
// =====================================

// Obtener mis pictogramas
router.get(
  "/mis-personalizados",
  verificarToken,
  obtenerMisPictogramasPersonalizados
);

// Crear personalizado mediante JSON
router.post(
  "/personalizado",
  verificarToken,
  crearPictogramaPersonalizado
);

// Crear personalizado subiendo una imagen
router.post(
  "/personalizado-con-imagen",
  verificarToken,
  upload.single("imagen"),
  crearPictogramaPersonalizadoConImagen
);

// Actualizar imagen de personalizado
router.put(
  "/personalizado/:id_pictograma/imagen",
  verificarToken,
  upload.single("imagen"),
  actualizarImagenPictogramaPersonalizado
);

// Actualizar datos de personalizado
router.put(
  "/personalizado/:id_pictograma",
  verificarToken,
  actualizarPictogramaPersonalizado
);

// Eliminar personalizado
router.delete(
  "/personalizado/:id_pictograma",
  verificarToken,
  eliminarPictogramaPersonalizado
);

// =====================================
// PICTOGRAMAS GENERALES: SOLO ADMIN
// =====================================

// Crear general con imagen
router.post(
  "/con-imagen",
  verificarToken,
  verificarAdmin,
  upload.single("imagen"),
  crearPictogramaConImagen
);

// Crear general mediante JSON
router.post(
  "/",
  verificarToken,
  verificarAdmin,
  crearPictograma
);

// Actualizar imagen general
router.put(
  "/:id_pictograma/imagen",
  verificarToken,
  verificarAdmin,
  upload.single("imagen"),
  actualizarImagenPictogramaGeneral
);

// Actualizar pictograma general
router.put(
  "/:id_pictograma",
  verificarToken,
  verificarAdmin,
  actualizarPictograma
);

// Eliminar pictograma general
router.delete(
  "/:id_pictograma",
  verificarToken,
  verificarAdmin,
  eliminarPictograma
);

module.exports = router;
