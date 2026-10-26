
const express = require("express");

const router = express.Router();

const {
  obtenerCategorias,
  obtenerMisCategorias,
  obtenerCategoriaPorId,
  crearCategoria,
  actualizarCategoria,
  eliminarCategoria,
  actualizarImagenCategoria
} = require("../controllers/categorias.controller");

const verificarToken = require("../middlewares/auth.middleware");
const upload = require("../middlewares/upload.middleware");

// ======================================
// CONSULTAR CATEGORÍAS
// ======================================

// Categorías generales
router.get("/", obtenerCategorias);

// Categorías generales + propias del usuario
router.get(
  "/mis-categorias",
  verificarToken,
  obtenerMisCategorias
);

// Categoría por ID
router.get("/:id_categoria", obtenerCategoriaPorId);

// ======================================
// CREAR CATEGORÍAS
// ======================================

// Crear categoría personal
router.post("/", verificarToken, crearCategoria);

// ======================================
// ACTUALIZAR CATEGORÍAS
// ======================================

// Subir o reemplazar imagen de una categoría
router.put(
  "/:id_categoria/imagen",
  verificarToken,
  (req, res, next) => {
    upload.single("imagen")(req, res, (error) => {
      if (error) {
        return res.status(
          error.code === "LIMIT_FILE_SIZE" ? 413 : 400
        ).json({
          data: null,
          error: error.code === "LIMIT_FILE_SIZE"
            ? "La imagen supera los 2 MB"
            : error.message
        });
      }

      next();
    });
  },
  actualizarImagenCategoria
);

// Actualizar nombre o color de categoría personal
router.put(
  "/:id_categoria",
  verificarToken,
  actualizarCategoria
);

// ======================================
// ELIMINAR CATEGORÍAS
// ======================================

// Eliminar categoría personal
router.delete(
  "/:id_categoria",
  verificarToken,
  eliminarCategoria
);

module.exports = router;
