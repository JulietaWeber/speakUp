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

const allowedOrigins = [
  "http://localhost:8081",
  "http://localhost:3000",
  "http://localhost:5173",
  "https://speak-up-two-tau.vercel.app"
];

app.use(cors({
  origin: function (origin, callback) {
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(null, true);
    }
  },
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"],
  credentials: false
}));

app.options(/.*/, cors());

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

module.exports = app;

if (require.main === module) {
  const PORT = process.env.PORT || 3000;

  app.listen(PORT, () => {
    console.log(`Servidor corriendo en puerto ${PORT}`);
  });
}