
import axios from "axios";

const API_URL = process.env.EXPO_PUBLIC_API_URL;

if (!API_URL) {
  console.warn("Falta configurar EXPO_PUBLIC_API_URL");
}

export type Pictograma = {
  id_pictogramas: number;
  id_categorias: number;
  nombre: string;
  imagen_url: string | null;
  audio_url: string | null;
  es_personalizado?: boolean;
};

export type ImagenExpo = {
  uri: string;
  name: string;
  type: string;
};

export type VozDisponible = {
  id: string;
  nombre: string;
  descripcion: string;
};

const getAuthHeaders = (token?: string) => {
  if (!token) return {};

  return {
    Authorization: `Bearer ${token}`,
  };
};

// =========================
// AUTENTICACIÓN
// =========================

export const login = async (
  email: string,
  password: string
) => {
  const response = await axios.post(
    `${API_URL}/auth/login`,
    { email, password }
  );

  return response.data.data;
};

export const register = async (
  nombre: string,
  email: string,
  password: string
) => {
  const response = await axios.post(
    `${API_URL}/auth/register`,
    { nombre, email, password }
  );

  return response.data.data;
};

// =========================
// CATEGORÍAS
// =========================

export const obtenerCategorias = async (token: string) => {
  const response = await axios.get(
    `${API_URL}/categorias/mis-categorias`,
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

export const crearCategoria = async (
  nombre: string,
  color: string,
  token: string
) => {
  const response = await axios.post(
    `${API_URL}/categorias`,
    { nombre, color },
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

// =========================
// PICTOGRAMAS
// =========================

export const obtenerPictogramas = async (
  token?: string
): Promise<Pictograma[]> => {
  const response = await axios.get(
    `${API_URL}/pictogramas`,
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

export const obtenerPictogramasPorCategoria = async (
  idCategoria: number,
  token: string
): Promise<Pictograma[]> => {
  const response = await axios.get(
    `${API_URL}/pictogramas/categoria/${idCategoria}`,
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

// =========================
// FRASES
// =========================

export const armarFrase = async (
  idUsuario: number,
  pictogramas: number[],
  token: string
) => {
  const response = await axios.post(
    `${API_URL}/frases/armar`,
    {
      id_usuario: idUsuario,
      pictogramas,
    },
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

// =========================
// PICTOGRAMA PERSONALIZADO
// =========================

export const crearPictogramaPersonalizado = async (
  idCategorias: number,
  nombre: string,
  token: string
) => {
  const response = await axios.post(
    `${API_URL}/pictogramas/personalizado`,
    {
      id_categorias: idCategorias,
      nombre,
    },
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

export const crearPictogramaPersonalizadoConImagen = async (
  idCategorias: number,
  nombre: string,
  imagen: ImagenExpo,
  token: string,
  audioUrl?: string
) => {
  const formData = new FormData();

  formData.append("id_categorias", String(idCategorias));
  formData.append("nombre", nombre);

  if (audioUrl) {
    formData.append("audio_url", audioUrl);
  }

  formData.append(
    "imagen",
    {
      uri: imagen.uri,
      name: imagen.name,
      type: imagen.type,
    } as any
  );

  const response = await axios.post(
    `${API_URL}/pictogramas/personalizado-con-imagen`,
    formData,
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

// =========================
// ACTUALIZAR IMAGEN
// =========================

export const actualizarImagenPictogramaPersonalizado = async (
  idPictograma: number,
  imagen: ImagenExpo,
  token: string
) => {
  const formData = new FormData();

  formData.append(
    "imagen",
    {
      uri: imagen.uri,
      name: imagen.name,
      type: imagen.type,
    } as any
  );

  const response = await axios.put(
    `${API_URL}/pictogramas/personalizado/${idPictograma}/imagen`,
    formData,
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

// =========================
// AUDIOS
// =========================

export const obtenerVoces = async (
  token: string
): Promise<VozDisponible[]> => {
  const response = await axios.get(
    `${API_URL}/audios/voces`,
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

export const actualizarVozPreferida = async (
  vozPreferida: string,
  token: string
) => {
  const response = await axios.put(
    `${API_URL}/usuarios/voz`,
    {
      voz_preferida: vozPreferida,
    },
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

export const generarAudio = async (
  idFrase: number,
  texto: string,
  token: string
) => {
  const inicio = Date.now();

  console.log("GENERANDO AUDIO...");
  console.log("Texto:", texto);

  const response = await axios.post(
    `${API_URL}/audios/generar`,
    {
      id_frase: idFrase,
      texto,
    },
    {
      headers: getAuthHeaders(token),
    }
  );

  const tiempo = Date.now() - inicio;

  console.log(`AUDIO GENERADO EN ${tiempo} ms`);

  return response.data.data;
};

// =========================
// INTELIGENCIA ARTIFICIAL
// =========================

export const corregirFraseIA = async (
  palabras: string[],
  token: string
) => {
  const response = await axios.post(
    `${API_URL}/ia/corregir`,
    { palabras },
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};

export const predecirPalabraIA = async (
  palabra: string,
  categoria: string,
  token: string
) => {
  const datos = {
    palabra: palabra.trim(),
    palabras: [palabra.trim()],
    categoria: categoria.trim(),
  };

  console.log("Datos enviados a la IA:", datos);

  const response = await axios.post(
    `${API_URL}/ia/predecir`,
    datos,
    {
      headers: {
        ...getAuthHeaders(token),
        "Content-Type": "application/json",
      },
    }
  );

  console.log("Respuesta recibida de la IA:", response.data);

  return response.data.data;
};

export const procesarFraseIA = async (
  palabras: string[],
  categoria: string,
  token: string
) => {
  const response = await axios.post(
    `${API_URL}/ia/procesar-frase`,
    {
      palabras,
      categoria,
    },
    {
      headers: getAuthHeaders(token),
    }
  );

  return response.data.data;
};
