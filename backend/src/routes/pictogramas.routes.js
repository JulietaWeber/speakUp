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
  crearPictogramaPersonalizadoConImagen
} = require("../controllers/pictogramas.controller");

const verificarToken = require("../middlewares/auth.middleware");
const verificarAdmin = require("../middlewares/admin.middleware");
const upload = require("../middlewares/upload.middleware");

router.get("/", obtenerPictogramas);

router.get("/categoria/:id_categoria", obtenerPictogramasPorCategoria);

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
  "/personalizado/:id_pictograma",
  verificarToken,
  actualizarPictogramaPersonalizado
);

router.delete(
  "/personalizado/:id_pictograma",
  verificarToken,
  eliminarPictogramaPersonalizado
);

router.post("/", verificarToken, verificarAdmin, crearPictograma);

router.put("/:id_pictograma", verificarToken, verificarAdmin, actualizarPictograma);

router.delete("/:id_pictograma", verificarToken, verificarAdmin, eliminarPictograma);

module.exports = router;