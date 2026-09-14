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

// Categorías generales
router.get("/", obtenerCategorias);

// Categorías generales + propias del usuario
router.get("/mis-categorias", verificarToken, obtenerMisCategorias);

// Categoría por ID
router.get("/:id_categoria", obtenerCategoriaPorId);

// Crear, editar y borrar categorías personales
router.post("/", verificarToken, crearCategoria);

router.put("/:id_categoria", verificarToken, actualizarCategoria);

router.delete("/:id_categoria", verificarToken, eliminarCategoria);

module.exports = router;