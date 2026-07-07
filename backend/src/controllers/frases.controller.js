const supabase = require("../config/Supabase");

const armarFrase = async (req, res) => {
  try {
    const { id_usuario, pictogramas } = req.body;

    if (!id_usuario) {
      return res.status(400).json({
        data: null,
        error: "Falta id_usuario"
      });
    }

    if (!Array.isArray(pictogramas) || pictogramas.length === 0) {
      return res.status(400).json({
        data: null,
        error: "Tenés que enviar al menos un pictograma"
      });
    }

    const { data: pictogramasData, error: pictogramasError } = await supabase
      .from("pictogramas")
      .select("id_pictogramas, nombre, imagen_url, audio_url")
      .in("id_pictogramas", pictogramas);

    if (pictogramasError) {
      return res.status(500).json({
        data: null,
        error: pictogramasError.message
      });
    }

    const pictogramasOrdenados = pictogramas
      .map((id) =>
        pictogramasData.find((p) => p.id_pictogramas === id)
      )
      .filter(Boolean);

    const texto = pictogramasOrdenados
      .map((p) => p.nombre)
      .join(" ");

    const { data: fraseCreada, error: fraseError } = await supabase
      .from("frases")
      .insert([
        {
          id_usuario,
          texto
        }
      ])
      .select()
      .single();

    if (fraseError) {
      return res.status(500).json({
        data: null,
        error: fraseError.message
      });
    }

    res.json({
      data: {
        id_frase: fraseCreada.id_frase,
        id_usuario,
        texto,
        pictogramas: pictogramasOrdenados
      },
      error: null
    });

  } catch (error) {
    res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

module.exports = {
  armarFrase
};