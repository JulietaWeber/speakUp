const supabase = require("../config/Supabase");

const armarFrase = async (req, res) => {
  try {
    const { pictogramas } = req.body;
    const id_usuario = req.usuario.id_usuario;

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
      .map((id) => pictogramasData.find((p) => p.id_pictogramas === id))
      .filter(Boolean);

    if (pictogramasOrdenados.length === 0) {
      return res.status(404).json({
        data: null,
        error: "No se encontraron pictogramas válidos"
      });
    }

    const texto = pictogramasOrdenados.map((p) => p.nombre).join(" ");

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

    const registrosFrasePictogramas = pictogramasOrdenados.map(
      (pictograma, index) => ({
        id_frase: fraseCreada.id_frase,
        id_pictogramas: pictograma.id_pictogramas,
        orden: index + 1
      })
    );

    const { error: frasePictogramasError } = await supabase
      .from("frase_pictogramas")
      .insert(registrosFrasePictogramas);

    if (frasePictogramasError) {
      return res.status(500).json({
        data: null,
        error: frasePictogramasError.message
      });
    }

    const { error: historialError } = await supabase
    .from("historial_uso")
    .insert([
    {
      id_usuario,
      accion: "armar_frase",
      detalle: texto
    }
  ]);

    if (historialError) {
    return res.status(500).json({
    data: null,
    error: historialError.message
  });
 }

    return res.json({
      data: {
        id_frase: fraseCreada.id_frase,
        id_usuario,
        texto,
        pictogramas: pictogramasOrdenados
      },
      error: null
    });
  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

const obtenerMisFrases = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data: frases, error } = await supabase
      .from("frases")
      .select(`
        id_frase,
        id_usuario,
        texto,
        fecha_creacion,
        frase_pictogramas (
          id_frase_pictogramas,
          orden,
          pictogramas (
            id_pictogramas,
            nombre,
            imagen_url,
            audio_url
          )
        )
      `)
      .eq("id_usuario", id_usuario)
      .order("fecha_creacion", { ascending: false });

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    const frasesOrdenadas = frases.map((frase) => ({
      ...frase,
      frase_pictogramas: frase.frase_pictogramas
        ? frase.frase_pictogramas.sort((a, b) => a.orden - b.orden)
        : []
    }));

    return res.json({
      data: frasesOrdenadas,
      error: null
    });
  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

module.exports = {
  armarFrase,
  obtenerMisFrases
};