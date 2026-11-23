
const express = require("express");
const router = express.Router();

const {
  obtenerCategorias,
  obtenerMisCategorias,
  obtenerCategoriaPorId,
  crearCategoria,
  actualizarCategoria,
  actualizarImagenCategoria,
  eliminarCategoria
} = require("../controllers/categorias.controller");

const verificarToken = require("../middlewares/auth.middleware");
const upload = require("../middlewares/upload.middleware");

// =====================================
// CONSULTAS PÚBLICAS
// =====================================

router.get("/", obtenerCategorias);

// =====================================
// CONSULTAS DEL USUARIO
// =====================================

router.get(
  "/mis-categorias",
  verificarToken,
  obtenerMisCategorias
);

// =====================================
// CREAR CATEGORÍA PERSONALIZADA
// =====================================

router.post(
  "/",
  verificarToken,
  crearCategoria
);

// =====================================
// ACTUALIZAR IMAGEN DE CATEGORÍA
// =====================================

router.put(
  "/:id_categoria/imagen",
  verificarToken,
  (req, res, next) => {
    upload.single("imagen")(req, res, (error) => {
      if (error) {
        const status =
          error.code === "LIMIT_FILE_SIZE"
            ? 413
            : 400;

        return res.status(status).json({
          data: null,
          error: error.message
        });
      }

      next();
    });
  },
  actualizarImagenCategoria
);

// =====================================
// CONSULTAR, EDITAR Y ELIMINAR POR ID
// =====================================

router.get(
  "/:id_categoria",
  obtenerCategoriaPorId
);

router.put(
  "/:id_categoria",
  verificarToken,
  actualizarCategoria
);

router.delete(
  "/:id_categoria",
  verificarToken,
  eliminarCategoria
);

module.exports = router;
