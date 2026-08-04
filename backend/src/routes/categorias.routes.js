const express = require("express");
const router = express.Router();

const {
  obtenerCategorias,
  obtenerMisCategorias,
  obtenerCategoriaPorId,
  crearCategoria,
  actualizarCategoria,
  eliminarCategoria
} = require("../controllers/categorias.controller");

const verificarToken = require("../middlewares/auth.middleware");

// GET público, devuelve categorías generales.
// Si querés ver generales + personales, usá token opcional más abajo.
router.get("/", obtenerCategorias);
router.get("/mis-categorias", verificarToken, obtenerMisCategorias);
router.get("/:id_categoria", obtenerCategoriaPorId);


// Crear, editar y borrar categorías personales requiere login.
router.post("/", verificarToken, crearCategoria);
router.put("/:id_categoria", verificarToken, actualizarCategoria);
router.delete("/:id_categoria", verificarToken, eliminarCategoria);

module.exports = router;