require("dotenv").config();

const express = require("express");
const cors = require("cors");

const usuariosRoutes = require("./routes/usuarios.routes");
const tablerosRoutes = require("./routes/tableros.routes");
const pictogramasRoutes = require("./routes/pictogramas.routes");
const categoriasRoutes = require("./routes/categorias.routes");
const frasesRoutes = require("./routes/frases.routes");
const authRoutes = require("./routes/auth.routes");
const historialUsoRoutes = require("./routes/historialUso.routes");
const sugerenciasRoutes = require("./routes/sugerencias.routes");
const audiosRoutes = require("./routes/audios.routes");

const app = express();

app.use(cors({
  origin: "*"
}));

app.use(express.json());

app.get("/", (req, res) => {
  res.json({
    data: "SpeakUp backend funcionando",
    error: null
  });
});

app.use("/usuarios", usuariosRoutes);
app.use("/tableros", tablerosRoutes);
app.use("/pictogramas", pictogramasRoutes);
app.use("/categorias", categoriasRoutes);
app.use("/frases", frasesRoutes);
app.use("/auth", authRoutes);
app.use("/historial-uso", historialUsoRoutes);
app.use("/sugerencias", sugerenciasRoutes);
app.use("/audios", audiosRoutes);

module.exports = app;

if (require.main === module) {
  const PORT = process.env.PORT || 3000;

  app.listen(PORT, () => {
    console.log(`Servidor corriendo en puerto ${PORT}`);
  });
}