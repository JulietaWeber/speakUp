require("dotenv").config();

const express = require("express");
const cors = require("cors");
const supabase = require("backend/src/config/supabase.js");

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.send("SpeakUp backend funcionando");
});

app.get("/test-db", async (req, res) => {
    const { data, error } = await supabase.from("users").select("*");
  
    res.json({ data, error });
  });

app.listen(3000, () => {
  console.log("Servidor corriendo en puerto 3000");
});