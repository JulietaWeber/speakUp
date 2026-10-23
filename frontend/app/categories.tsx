import { useEffect, useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
  ScrollView,
  ActivityIndicator,
  TextInput,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Modal,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { Ionicons } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";

import ConstructionBar from "../components/ConstructionBar";
import { useConstruction } from "../context/ConstructionContext";

import {
  obtenerCategorias,
  obtenerPictogramasPorCategoria,
  crearCategoria,
  crearPictogramaPersonalizado,
  crearPictogramaPersonalizadoConImagen,
  procesarFraseIA,
  obtenerVoces,
  actualizarVozPreferida,
  type VozDisponible,
} from "../services/api";

export default function Categories() {
  const { palabras, agregarPalabra, reemplazarPalabras } =
    useConstruction();

  const [categories, setCategories] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<any | null>(null);
  const [pictograms, setPictograms] = useState<any[]>([]);
  const [loadingPictograms, setLoadingPictograms] = useState(false);

  const [mostrarConfiguracion, setMostrarConfiguracion] = useState(false);
  const [voces, setVoces] = useState<VozDisponible[]>([]);
  const [vozSeleccionada, setVozSeleccionada] = useState<string | null>(null);
  const [cargandoVoces, setCargandoVoces] = useState(false);
  const [guardandoVoz, setGuardandoVoz] = useState(false);

  const [sugerenciasIA, setSugerenciasIA] = useState<any[]>([]);
  const [fraseCorregidaIA, setFraseCorregidaIA] = useState<string | null>(null);
  const [consultandoFraseIA, setConsultandoFraseIA] = useState(false);
  const [sugerenciasCargadas, setSugerenciasCargadas] = useState(false);

  const [mostrarAgregarPalabra, setMostrarAgregarPalabra] = useState(false);
  const [nuevoNombre, setNuevoNombre] = useState("");
  const [mostrarAgregarCategoria, setMostrarAgregarCategoria] = useState(false);
  const [nuevoNombreCategoria, setNuevoNombreCategoria] = useState("");
  const [guardandoPalabra, setGuardandoPalabra] = useState(false);
  const [guardandoCategoria, setGuardandoCategoria] = useState(false);

  const [imagenNuevaPalabra, setImagenNuevaPalabra] = useState<any | null>(null);

  const coloresDisponibles = [
    "#FF6B6B",
    "#FF9F43",
    "#FFD166",
    "#6BCB77",
    "#4ECDC4",
    "#45B7D1",
    "#5B8DEF",
    "#7B61FF",
    "#C77DFF",
    "#FF70A6",
    "#356879",
    "#8D99AE",
  ];

  const [colorSeleccionado, setColorSeleccionado] = useState("#356879");

  // RECUPERAR SUGERENCIAS Y FRASE CORREGIDA GUARDADAS

  useEffect(() => {
    const cargarDatosIA = async () => {
      try {
        const datosGuardados = await AsyncStorage.getItem("datos_ia");

        if (datosGuardados) {
          const datos = JSON.parse(datosGuardados);

          if (Array.isArray(datos.sugerencias)) {
            setSugerenciasIA(datos.sugerencias);
          }

          if (
            typeof datos.fraseCorregida === "string" &&
            datos.fraseCorregida.trim()
          ) {
            setFraseCorregidaIA(datos.fraseCorregida);
          }
        } else {
          const sugerenciasAnteriores = await AsyncStorage.getItem(
            "sugerencias_ia"
          );

          if (sugerenciasAnteriores) {
            const sugerencias = JSON.parse(sugerenciasAnteriores);

            if (Array.isArray(sugerencias)) {
              setSugerenciasIA(sugerencias);
            }
          }
        }
      } catch (error) {
        console.error("Error recuperando los datos de IA:", error);
      } finally {
        setSugerenciasCargadas(true);
      }
    };

    cargarDatosIA();
  }, []);

  // GUARDAR SUGERENCIAS Y FRASE CORREGIDA CADA VEZ QUE CAMBIAN

  useEffect(() => {
    if (!sugerenciasCargadas) return;

    const guardarDatosIA = async () => {
      try {
        await AsyncStorage.setItem(
          "datos_ia",
          JSON.stringify({
            sugerencias: sugerenciasIA,
            fraseCorregida: fraseCorregidaIA,
          })
        );
      } catch (error) {
        console.error("Error guardando los datos de IA:", error);
      }
    };

    guardarDatosIA();
  }, [sugerenciasIA, fraseCorregidaIA, sugerenciasCargadas]);

  // CONFIGURACIÓN DE VOZ

  const abrirConfiguracion = async () => {
    setMostrarConfiguracion(true);
    setCargandoVoces(true);

    try {
      const token = await AsyncStorage.getItem("token");

      if (!token) {
        Alert.alert(
          "Sesión vencida",
          "Volvé a iniciar sesión para configurar tu voz."
        );
        setMostrarConfiguracion(false);
        return;
      }

      const [vocesDisponibles, vozGuardada] = await Promise.all([
        obtenerVoces(token),
        AsyncStorage.getItem("voz_preferida"),
      ]);

      if (!Array.isArray(vocesDisponibles)) {
        throw new Error("La respuesta de voces no tiene el formato esperado.");
      }

      setVoces(vocesDisponibles);

      if (vozGuardada && vocesDisponibles.some((voz) => voz.id === vozGuardada)) {
        setVozSeleccionada(vozGuardada);
      } else {
        setVozSeleccionada(null);
      }
    } catch (error: any) {
      console.error(
        "Error al cargar las voces:",
        error?.response?.data || error?.message || error
      );
      Alert.alert(
        "Error",
        "No se pudieron cargar las voces. Revisá tu conexión e intentá nuevamente."
      );
    } finally {
      setCargandoVoces(false);
    }
  };

  const guardarVoz = async (vozId: string) => {
    if (guardandoVoz) return;

    try {
      setGuardandoVoz(true);
      const token = await AsyncStorage.getItem("token");

      if (!token) {
        Alert.alert(
          "Sesión vencida",
          "Volvé a iniciar sesión para guardar tu voz."
        );
        return;
      }

      const usuarioActualizado = await actualizarVozPreferida(vozId, token);
      const vozConfirmada = usuarioActualizado?.voz_preferida || vozId;

      await AsyncStorage.setItem("voz_preferida", vozConfirmada);
      setVozSeleccionada(vozConfirmada);

      Alert.alert(
        "Voz actualizada",
        "Tu voz preferida fue guardada correctamente."
      );
    } catch (error: any) {
      console.error(
        "Error al guardar la voz:",
        error?.response?.data || error?.message || error
      );
      Alert.alert(
        "Error",
        error?.response?.data?.error || "No se pudo guardar tu voz preferida."
      );
    } finally {
      setGuardandoVoz(false);
    }
  };

  // CARGAR CATEGORÍAS

  useEffect(() => {
    const cargarCategorias = async () => {
      try {
        const token = await AsyncStorage.getItem("token");

        if (!token) {
          console.log("No hay token");
          return;
        }

        const data = await obtenerCategorias(token);
        setCategories(data);
        setSelectedCategory(null);
        setPictograms([]);
      } catch (error) {
        console.error("Error cargando categorías:", error);
      }
    };

    cargarCategorias();
  }, []);

  // CARGAR PICTOGRAMAS DE LA CATEGORÍA SELECCIONADA

  useEffect(() => {
    const cargarPictogramas = async () => {
      if (!selectedCategory) {
        setPictograms([]);
        return;
      }

      try {
        setLoadingPictograms(true);
        const token = await AsyncStorage.getItem("token");

        if (!token) {
          console.log("No hay token");
          return;
        }

        const data = await obtenerPictogramasPorCategoria(
          selectedCategory.id_categorias,
          token
        );

        setPictograms(data);
      } catch (error) {
        console.error("Error cargando pictogramas:", error);
        setPictograms([]);
      } finally {
        setLoadingPictograms(false);
      }
    };

    cargarPictogramas();
  }, [selectedCategory]);

  // COLOR SUAVE PARA LA VISTA PREVIA

  const getBackgroundColor = (color: string) => {
    if (!color) return "#F2F6F7";

    if (color.startsWith("#")) {
      const hex = color.replace("#", "");
      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);

      const softR = Math.round(r + (255 - r) * 0.78);
      const softG = Math.round(g + (255 - g) * 0.78);
      const softB = Math.round(b + (255 - b) * 0.78);

      return `rgb(${softR}, ${softG}, ${softB})`;
    }

    return "#F2F6F7";
  };

  // ENTRAR A UNA CATEGORÍA

  const seleccionarCategoria = (category: any) => {
    setSelectedCategory(category);
    setMostrarAgregarPalabra(false);
    setNuevoNombre("");
    setImagenNuevaPalabra(null);
    setMostrarAgregarCategoria(false);
    setNuevoNombreCategoria("");
    setColorSeleccionado("#356879");
  };

  // VOLVER A LA GRILLA DE CATEGORÍAS

  const volverACategorias = () => {
    setSelectedCategory(null);
    setPictograms([]);
    setMostrarAgregarPalabra(false);
    setNuevoNombre("");
    setImagenNuevaPalabra(null);
    setMostrarAgregarCategoria(false);
    setNuevoNombreCategoria("");
  };

  // AGREGAR PICTOGRAMA A LA FRASE Y CONSULTAR LA IA

  const agregarPictograma = async (pictogram: any) => {
    const palabrasActualizadas = [...palabras, pictogram];

    agregarPalabra(pictogram);
    setFraseCorregidaIA(null);

    try {
      const token = await AsyncStorage.getItem("token");

      if (!token || !selectedCategory) {
        console.log("Falta el token o la categoría seleccionada");
        return;
      }

      const palabrasTexto = palabrasActualizadas
        .map((palabra: any) => palabra.nombre)
        .filter(Boolean);

      if (palabrasTexto.length === 0) return;

      setConsultandoFraseIA(true);
      console.log("Consultando IA para la frase:", palabrasTexto);

      const respuesta = await procesarFraseIA(
        palabrasTexto,
        selectedCategory.nombre || "general",
        token
      );

      console.log("Respuesta de la IA:", respuesta);

      setFraseCorregidaIA(
        typeof respuesta?.frase_corregida === "string" &&
          respuesta.frase_corregida.trim()
          ? respuesta.frase_corregida.trim()
          : null
      );

      setSugerenciasIA(
        Array.isArray(respuesta?.predicciones) ? respuesta.predicciones : []
      );
    } catch (error: any) {
      setSugerenciasIA([]);
      setFraseCorregidaIA(null);

      console.error(
        "Error al consultar la IA:",
        JSON.stringify(error?.response?.data || error?.message || error, null, 2)
      );
    } finally {
      setConsultandoFraseIA(false);
    }
  };

  const aceptarFraseCorregida = () => {
    if (!fraseCorregidaIA) return;

    const palabrasOriginales = [...palabras];

    const palabrasCorregidas = fraseCorregidaIA
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .map((texto: string) => {
        const normalizar = (valor: string) =>
          valor.toLocaleLowerCase().replace(/[.,!?¿¡;:]/g, "");

        const coincidencia = palabrasOriginales.find(
          (palabra: any) =>
            normalizar(String(palabra.nombre || "")) === normalizar(texto)
        );

        if (coincidencia) return coincidencia;

        return {
          nombre: texto,
          id_pictogramas: null,
          es_sugerencia_ia: true as const,
        };
      });

    reemplazarPalabras(palabrasCorregidas);
    setFraseCorregidaIA(null);
    setSugerenciasIA([]);
  };

  // ELEGIR FOTO PARA UNA PALABRA

  const elegirFoto = async () => {
    try {
      const permiso = await ImagePicker.requestMediaLibraryPermissionsAsync();

      if (!permiso.granted) {
        Alert.alert(
          "Permiso necesario",
          "Necesitamos permiso para acceder a tus fotos y elegir una imagen para la palabra."
        );
        return;
      }

      const resultado = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (resultado.canceled) return;

      const asset = resultado.assets[0];
      if (!asset) return;

      setImagenNuevaPalabra({
        uri: asset.uri,
        name: asset.fileName || `pictograma-${Date.now()}.jpg`,
        type: asset.mimeType || "image/jpeg",
      });
    } catch (error) {
      console.error("Error seleccionando imagen:", error);
      Alert.alert("Error", "No se pudo seleccionar la imagen.");
    }
  };

  const quitarFoto = () => setImagenNuevaPalabra(null);

  // CREAR NUEVA PALABRA

  const guardarNuevaPalabra = async () => {
    if (!nuevoNombre.trim()) {
      Alert.alert("Falta el nombre", "Escribí el nombre de la nueva palabra.");
      return;
    }

    if (!selectedCategory) {
      Alert.alert(
        "Seleccioná una categoría",
        "Primero seleccioná la categoría donde querés guardar la palabra."
      );
      return;
    }

    try {
      setGuardandoPalabra(true);
      const token = await AsyncStorage.getItem("token");

      if (!token) {
        Alert.alert("Error", "No se encontró el token del usuario.");
        return;
      }

      let nuevaPalabra;

      if (imagenNuevaPalabra) {
        nuevaPalabra = await crearPictogramaPersonalizadoConImagen(
          selectedCategory.id_categorias,
          nuevoNombre.trim(),
          imagenNuevaPalabra,
          token
        );
      } else {
        nuevaPalabra = await crearPictogramaPersonalizado(
          selectedCategory.id_categorias,
          nuevoNombre.trim(),
          token
        );
      }

      setPictograms((prev) => [...prev, nuevaPalabra]);
      setNuevoNombre("");
      setImagenNuevaPalabra(null);
      setMostrarAgregarPalabra(false);

      Alert.alert(
        "Palabra agregada",
        `"${nuevaPalabra.nombre}" fue agregada a ${selectedCategory.nombre}.`
      );
    } catch (error: any) {
      console.error("Error creando palabra:", error);
      console.error("Respuesta backend:", error?.response?.data);

      Alert.alert(
        "Error",
        error?.response?.data?.error || "No se pudo crear la nueva palabra."
      );
    } finally {
      setGuardandoPalabra(false);
    }
  };

  // CREAR NUEVA CATEGORÍA

  const guardarNuevaCategoria = async () => {
    if (!nuevoNombreCategoria.trim()) {
      Alert.alert("Falta el nombre", "Escribí el nombre de la nueva categoría.");
      return;
    }

    try {
      setGuardandoCategoria(true);
      const token = await AsyncStorage.getItem("token");

      if (!token) {
        Alert.alert("Error", "No se encontró el token del usuario.");
        return;
      }

      const nuevaCategoria = await crearCategoria(
        nuevoNombreCategoria.trim(),
        colorSeleccionado,
        token
      );

      setCategories((prev) => [...prev, nuevaCategoria]);
      setSelectedCategory(nuevaCategoria);
      setPictograms([]);
      setNuevoNombreCategoria("");
      setColorSeleccionado("#356879");
      setMostrarAgregarCategoria(false);

      Alert.alert(
        "Categoría creada",
        `"${nuevaCategoria.nombre}" fue creada correctamente.`
      );
    } catch (error: any) {
      console.error("Error creando categoría:", error);
      console.error("Respuesta backend:", error?.response?.data);

      Alert.alert(
        "Error",
        error?.response?.data?.error || "No se pudo crear la nueva categoría."
      );
    } finally {
      setGuardandoCategoria(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.keyboardContainer}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 35}
    >
      <View style={styles.container}>
        {/* HEADER */}

        <View style={styles.header}>
          <Text style={styles.headerTitle}>Speak Up</Text>

          <TouchableOpacity
            style={styles.settingsButton}
            onPress={abrirConfiguracion}
            activeOpacity={0.75}
            accessibilityRole="button"
            accessibilityLabel="Configuración de voz"
          >
            <Ionicons name="settings-outline" size={25} color="#FFFFFF" />
          </TouchableOpacity>
        </View>

        {/* CONFIGURACIÓN DE VOZ */}

        <Modal
          visible={mostrarConfiguracion}
          transparent
          animationType="fade"
          onRequestClose={() => {
            if (!guardandoVoz) setMostrarConfiguracion(false);
          }}
        >
          <View style={styles.modalFondo}>
            <View style={styles.modalContenido}>
              <View style={styles.modalEncabezado}>
                <Text style={styles.modalTitulo}>Configuración</Text>

                <TouchableOpacity
                  onPress={() => setMostrarConfiguracion(false)}
                  disabled={guardandoVoz}
                  accessibilityRole="button"
                  accessibilityLabel="Cerrar configuración"
                >
                  <Ionicons name="close" size={26} color="#356879" />
                </TouchableOpacity>
              </View>

              <Text style={styles.modalSubtitulo}>
                Elegí la voz con la que Speak Up leerá tus frases.
              </Text>

              {cargandoVoces ? (
                <View style={styles.modalCargando}>
                  <ActivityIndicator size="large" color="#356879" />
                  <Text style={styles.modalCargandoTexto}>Cargando voces...</Text>
                </View>
              ) : voces.length === 0 ? (
                <View style={styles.modalVacio}>
                  <Text style={styles.modalVacioTexto}>
                    No se pudieron mostrar las voces.
                  </Text>

                  <TouchableOpacity
                    style={styles.reintentarButton}
                    onPress={abrirConfiguracion}
                    disabled={guardandoVoz}
                  >
                    <Text style={styles.reintentarTexto}>
                      Intentar nuevamente
                    </Text>
                  </TouchableOpacity>
                </View>
              ) : (
                voces.map((voz) => (
                  <TouchableOpacity
                    key={voz.id}
                    style={[
                      styles.opcionVoz,
                      vozSeleccionada === voz.id && styles.opcionVozSeleccionada,
                    ]}
                    disabled={guardandoVoz}
                    activeOpacity={0.75}
                    onPress={() => guardarVoz(voz.id)}
                  >
                    <View style={styles.opcionVozTexto}>
                      <Text style={styles.nombreVoz}>{voz.nombre}</Text>
                      <Text style={styles.descripcionVoz}>
                        {voz.descripcion}
                      </Text>
                    </View>

                    {vozSeleccionada === voz.id && (
                      <Ionicons
                        name="checkmark-circle"
                        size={24}
                        color="#356879"
                      />
                    )}
                  </TouchableOpacity>
                ))
              )}

              {guardandoVoz && (
                <View style={styles.guardandoVoz}>
                  <ActivityIndicator color="#356879" />
                  <Text style={styles.guardandoVozTexto}>
                    Guardando tu elección...
                  </Text>
                </View>
              )}
            </View>
          </View>
        </Modal>

        {/* CONTENIDO */}

        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <ConstructionBar />

          {consultandoFraseIA && (
            <View style={styles.fraseIACargando}>
              <ActivityIndicator size="small" color="#356879" />
              <Text style={styles.fraseIATexto}>Revisando la frase...</Text>
            </View>
          )}

          {fraseCorregidaIA && (
            <View style={styles.fraseIASugerida}>
              <Text style={styles.fraseIATitulo}>Sugerencia de Speak Up</Text>
              <Text style={styles.fraseIATexto}>{fraseCorregidaIA}</Text>

              <View style={styles.fraseIABotones}>
                <TouchableOpacity
                  style={styles.fraseIARechazar}
                  activeOpacity={0.75}
                  onPress={() => setFraseCorregidaIA(null)}
                >
                  <Ionicons name="close" size={17} color="#5F6B70" />
                  <Text style={styles.fraseIARechazarTexto}>
                    Mantener mi frase
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.fraseIAAceptar}
                  activeOpacity={0.75}
                  onPress={aceptarFraseCorregida}
                >
                  <Ionicons name="checkmark" size={17} color="#FFFFFF" />
                  <Text style={styles.fraseIAAceptarTexto}>
                    Usar sugerencia
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* SUGERENCIAS DE LA IA */}

          {sugerenciasIA.length > 0 && (
            <View style={styles.sugerenciasContainer}>
              <Text style={styles.sugerenciasTitulo}>
                Recientes y sugeridos
              </Text>

              <View style={styles.sugerenciasLista}>
                {sugerenciasIA.map((sugerencia, index) => {
                  const palabra = String(sugerencia.palabra || "");
                  const palabraLower = palabra.toLowerCase();

                  const icono = /si|sí|bueno|bien|quiero|gracias/.test(
                    palabraLower
                  )
                    ? "checkmark"
                    : /no|nunca|mal/.test(palabraLower)
                    ? "close"
                    : /hola|salud|chau|adiós/.test(palabraLower)
                    ? "hand-left-outline"
                    : "chatbubble-ellipses-outline";

                  return (
                    <TouchableOpacity
                      key={`${sugerencia.palabra}-${index}`}
                      activeOpacity={0.75}
                      style={styles.sugerenciaChip}
                      onPress={() => {
                        agregarPalabra({
                          nombre: sugerencia.palabra,
                          id_pictogramas: null,
                          es_sugerencia_ia: true,
                        } as any);

                        setSugerenciasIA((prev) =>
                          prev.filter((_, i) => i !== index)
                        );
                      }}
                    >
                      <Ionicons
                        name={icono as any}
                        size={17}
                        color="#356879"
                      />
                      <Text style={styles.sugerenciaTexto} numberOfLines={1}>
                        {sugerencia.palabra}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>
          )}

          {/* PANTALLA PRINCIPAL: CATEGORÍAS */}

          {!selectedCategory && (
            <>
              <Text style={styles.categoriesTitle}>Categorías</Text>

              <View style={styles.categoriesContainer}>
                {categories.map((cat) => (
                  <TouchableOpacity
                    key={cat.id_categorias}
                    activeOpacity={0.75}
                    onPress={() => seleccionarCategoria(cat)}
                    style={[
                      styles.categoryButton,
                      {
                        backgroundColor: "#FFFFFF",
                        borderColor: "#D9C8C8",
                      },
                    ]}
                  >
                    <Text style={styles.categoryText}>{cat.nombre}</Text>
                  </TouchableOpacity>
                ))}

                {!mostrarAgregarCategoria && (
                  <TouchableOpacity
                    style={styles.newCategoryButton}
                    activeOpacity={0.75}
                    onPress={() => {
                      setMostrarAgregarCategoria(true);
                      setColorSeleccionado("#356879");
                    }}
                    accessibilityRole="button"
                    accessibilityLabel="Agregar nueva categoría"
                  >
                    <Ionicons name="add" size={34} color="#356879" />
                  </TouchableOpacity>
                )}
              </View>

              {/* FORMULARIO DE NUEVA CATEGORÍA */}

              {mostrarAgregarCategoria && (
                <View style={styles.newCategoryContainer}>
                  <Text style={styles.newCategoryTitle}>Nueva categoría</Text>

                  <TextInput
                    value={nuevoNombreCategoria}
                    onChangeText={setNuevoNombreCategoria}
                    placeholder="Escribí el nombre de la categoría"
                    placeholderTextColor="#9AA8AD"
                    style={styles.newCategoryInput}
                  />

                  <Text style={styles.colorTitle}>Elegí un color</Text>

                  <View style={styles.colorsContainer}>
                    {coloresDisponibles.map((color) => {
                      const seleccionado = colorSeleccionado === color;

                      return (
                        <TouchableOpacity
                          key={color}
                          activeOpacity={0.7}
                          onPress={() => setColorSeleccionado(color)}
                          style={[
                            styles.colorCircle,
                            { backgroundColor: color },
                            seleccionado && styles.selectedColorCircle,
                          ]}
                        >
                          {seleccionado && (
                            <Ionicons
                              name="checkmark"
                              size={21}
                              color="#FFFFFF"
                            />
                          )}
                        </TouchableOpacity>
                      );
                    })}
                  </View>

                  <View style={styles.previewContainer}>
                    <Text style={styles.previewLabel}>Vista previa</Text>

                    <View
                      style={[
                        styles.previewCategory,
                        {
                          backgroundColor: getBackgroundColor(colorSeleccionado),
                          borderColor: colorSeleccionado,
                        },
                      ]}
                    >
                      <View
                        style={[
                          styles.previewDot,
                          { backgroundColor: colorSeleccionado },
                        ]}
                      />
                      <Text
                        style={[
                          styles.previewText,
                          { color: colorSeleccionado },
                        ]}
                      >
                        {nuevoNombreCategoria.trim() || "Mi categoría"}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.newCategoryButtons}>
                    <TouchableOpacity
                      style={styles.cancelButton}
                      activeOpacity={0.75}
                      onPress={() => {
                        setMostrarAgregarCategoria(false);
                        setNuevoNombreCategoria("");
                        setColorSeleccionado("#356879");
                      }}
                    >
                      <Text style={styles.cancelButtonText}>Cancelar</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={[
                        styles.saveButton,
                        guardandoCategoria && styles.disabledButton,
                      ]}
                      activeOpacity={0.75}
                      disabled={guardandoCategoria}
                      onPress={guardarNuevaCategoria}
                    >
                      {guardandoCategoria ? (
                        <ActivityIndicator size="small" color="#FFFFFF" />
                      ) : (
                        <>
                          <Ionicons
                            name="checkmark"
                            size={18}
                            color="#FFFFFF"
                          />
                          <Text style={styles.saveButtonText}>Guardar</Text>
                        </>
                      )}
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </>
          )}

          {/* PANTALLA INTERNA DE LA CATEGORÍA */}

          {selectedCategory && (
            <>
              <View style={styles.selectedCategoryContainer}>
                <TouchableOpacity
                  style={styles.backButton}
                  activeOpacity={0.75}
                  onPress={volverACategorias}
                  accessibilityRole="button"
                  accessibilityLabel="Volver a las categorías"
                >
                  <Ionicons name="arrow-back" size={24} color="#356879" />
                </TouchableOpacity>

                <Text style={styles.selectedCategoryTitle}>
                  {selectedCategory.nombre}
                </Text>
              </View>

              {/* PICTOGRAMAS DE LA CATEGORÍA */}

              {loadingPictograms ? (
                <View style={styles.loadingContainer}>
                  <ActivityIndicator size="large" color="#356879" />
                  <Text style={styles.loadingText}>
                    Cargando pictogramas...
                  </Text>
                </View>
              ) : (
                <>
                  <View style={styles.pictogramsContainer}>
                    {pictograms.map((pictogram) => (
                      <TouchableOpacity
                        key={pictogram.id_pictogramas}
                        activeOpacity={0.75}
                        style={styles.pictogramButton}
                        onPress={() => agregarPictograma(pictogram)}
                      >
                        {pictogram.imagen_url ? (
                          <Image
                            source={{ uri: pictogram.imagen_url }}
                            style={styles.pictogramImage}
                            resizeMode="contain"
                          />
                        ) : (
                          <View style={styles.noImageContainer}>
                            <Ionicons
                              name="image-outline"
                              size={35}
                              color="#AAB7BC"
                            />
                          </View>
                        )}

                        <Text style={styles.pictogramText} numberOfLines={2}>
                          {pictogram.nombre}
                        </Text>
                      </TouchableOpacity>
                    ))}

                    {!mostrarAgregarPalabra && (
                      <TouchableOpacity
                        style={styles.newWordButton}
                        activeOpacity={0.75}
                        onPress={() => {
                          setMostrarAgregarPalabra(true);
                          setImagenNuevaPalabra(null);
                        }}
                        accessibilityRole="button"
                        accessibilityLabel="Agregar nueva palabra"
                      >
                        <Ionicons name="add" size={34} color="#356879" />
                      </TouchableOpacity>
                    )}
                  </View>

                  {pictograms.length === 0 && (
                    <View style={styles.emptyPictogramsContainer}>
                      <Ionicons
                        name="images-outline"
                        size={45}
                        color="#AAB7BC"
                      />
                      <Text style={styles.emptyText}>
                        Esta categoría todavía no tiene pictogramas
                      </Text>
                    </View>
                  )}

                  {/* FORMULARIO DE NUEVA PALABRA */}

                  {mostrarAgregarPalabra && (
                    <View style={styles.newWordContainer}>
                      <Text style={styles.newWordTitle}>Nueva palabra</Text>

                      <TextInput
                        value={nuevoNombre}
                        onChangeText={setNuevoNombre}
                        placeholder="Escribí una palabra"
                        placeholderTextColor="#9AA8AD"
                        style={styles.newWordInput}
                      />

                      <TouchableOpacity
                        style={styles.imagePickerButton}
                        activeOpacity={0.75}
                        onPress={elegirFoto}
                      >
                        {imagenNuevaPalabra ? (
                          <>
                            <Image
                              source={{ uri: imagenNuevaPalabra.uri }}
                              style={styles.selectedImage}
                              resizeMode="cover"
                            />

                            <View style={styles.imageInfo}>
                              <Ionicons
                                name="checkmark-circle"
                                size={22}
                                color="#6BCB77"
                              />
                              <Text
                                style={styles.imageSelectedText}
                                numberOfLines={1}
                              >
                                Foto seleccionada
                              </Text>
                            </View>

                            <TouchableOpacity
                              style={styles.removeImageButton}
                              activeOpacity={0.75}
                              onPress={quitarFoto}
                            >
                              <Ionicons
                                name="close-circle"
                                size={25}
                                color="#FF6B6B"
                              />
                            </TouchableOpacity>
                          </>
                        ) : (
                          <>
                            <View style={styles.imageIconContainer}>
                              <Ionicons
                                name="image-outline"
                                size={28}
                                color="#356879"
                              />
                            </View>
                            <View>
                              <Text style={styles.imagePickerTitle}>
                                Agregar una foto
                              </Text>
                              <Text style={styles.imagePickerSubtitle}>
                                Elegí una imagen de tu galería
                              </Text>
                            </View>
                          </>
                        )}
                      </TouchableOpacity>

                      <View style={styles.newWordButtons}>
                        <TouchableOpacity
                          style={styles.cancelButton}
                          activeOpacity={0.75}
                          onPress={() => {
                            setMostrarAgregarPalabra(false);
                            setNuevoNombre("");
                            setImagenNuevaPalabra(null);
                          }}
                        >
                          <Text style={styles.cancelButtonText}>Cancelar</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                          style={[
                            styles.saveButton,
                            guardandoPalabra && styles.disabledButton,
                          ]}
                          activeOpacity={0.75}
                          disabled={guardandoPalabra}
                          onPress={guardarNuevaPalabra}
                        >
                          {guardandoPalabra ? (
                            <ActivityIndicator size="small" color="#FFFFFF" />
                          ) : (
                            <>
                              <Ionicons
                                name="checkmark"
                                size={18}
                                color="#FFFFFF"
                              />
                              <Text style={styles.saveButtonText}>Guardar</Text>
                            </>
                          )}
                        </TouchableOpacity>
                      </View>
                    </View>
                  )}
                </>
              )}
            </>
          )}
        </ScrollView>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  keyboardContainer: { flex: 1 },
  container: { flex: 1, backgroundColor: "#EEF3F5" },
  scroll: { flex: 1 },
  content: { paddingHorizontal: 8, paddingTop: 10, paddingBottom: 60 },

  header: {
    height: 90,
    backgroundColor: "#356879",
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-between",
    paddingHorizontal: 15,
    paddingBottom: 8,
  },
  headerTitle: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "bold",
    paddingBottom: 8,
  },
  settingsButton: {
    justifyContent: "center",
    alignItems: "center",
    paddingBottom: 8,
  },

  modalFondo: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.4)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  modalContenido: {
    width: "100%",
    maxWidth: 420,
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 20,
  },
  modalEncabezado: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  modalTitulo: { fontSize: 22, fontWeight: "700", color: "#356879" },
  modalSubtitulo: {
    fontSize: 14,
    color: "#5F6B70",
    marginBottom: 18,
    lineHeight: 20,
  },
  modalCargando: { alignItems: "center", paddingVertical: 20 },
  modalCargandoTexto: { marginTop: 10, color: "#5F6B70", fontSize: 13 },
  modalVacio: { alignItems: "center", paddingVertical: 15 },
  modalVacioTexto: {
    color: "#5F6B70",
    fontSize: 13,
    textAlign: "center",
  },
  reintentarButton: {
    marginTop: 12,
    backgroundColor: "#356879",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
  },
  reintentarTexto: { color: "#FFFFFF", fontSize: 13, fontWeight: "700" },
  opcionVoz: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#D9E2E5",
    marginBottom: 10,
    backgroundColor: "#FFFFFF",
  },
  opcionVozSeleccionada: {
    borderColor: "#356879",
    backgroundColor: "#EEF5F6",
  },
  opcionVozTexto: { flex: 1 },
  nombreVoz: { fontSize: 15, fontWeight: "700", color: "#356879" },
  descripcionVoz: {
    fontSize: 12,
    color: "#718187",
    marginTop: 4,
    lineHeight: 17,
  },
  guardandoVoz: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
    gap: 8,
  },
  guardandoVozTexto: { color: "#5F6B70", fontSize: 12 },

  categoriesTitle: {
    fontSize: 13,
    color: "#356879",
    fontWeight: "600",
    marginBottom: 8,
    marginLeft: 2,
  },
  categoriesContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "flex-start",
    gap: 10,
  },
  categoryButton: {
    width: "31%",
    minHeight: 82,
    borderRadius: 14,
    borderWidth: 2,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 8,
    paddingVertical: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 2,
    elevation: 2,
  },
  categoryText: {
    fontSize: 12,
    textAlign: "center",
    fontWeight: "600",
    color: "#5F6B70",
  },

  newCategoryButton: {
    width: "31%",
    minHeight: 82,
    borderWidth: 1,
    borderColor: "#356879",
    borderRadius: 14,
    backgroundColor: "#FFFFFF",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 8,
    paddingVertical: 8,
  },
  newCategoryButtonText: {
    fontSize: 10,
    fontWeight: "600",
    color: "#356879",
    marginTop: 4,
    textAlign: "center",
  },
  newCategoryContainer: {
    marginTop: 15,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 15,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.07,
    shadowRadius: 2,
    elevation: 2,
  },
  newCategoryTitle: {
    fontSize: 16,
    color: "#356879",
    fontWeight: "700",
    marginBottom: 10,
  },
  newCategoryInput: {
    height: 45,
    borderWidth: 1,
    borderColor: "#C8D3D7",
    borderRadius: 10,
    paddingHorizontal: 12,
    fontSize: 14,
    color: "#5F6B70",
    backgroundColor: "#F8FAFB",
  },
  colorTitle: {
    fontSize: 13,
    color: "#356879",
    fontWeight: "700",
    marginTop: 16,
    marginBottom: 10,
  },
  colorsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
    alignItems: "center",
  },
  colorCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 2,
    borderColor: "#FFFFFF",
  },
  selectedColorCircle: {
    borderColor: "#FFFFFF",
    borderWidth: 3,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
    elevation: 4,
  },
  previewContainer: { marginTop: 17 },
  previewLabel: { fontSize: 11, color: "#7A898F", marginBottom: 7 },
  previewCategory: {
    minHeight: 50,
    borderRadius: 12,
    borderWidth: 2,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
  },
  previewDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    marginRight: 9,
  },
  previewText: { fontSize: 13, fontWeight: "700" },
  newCategoryButtons: {
    flexDirection: "row",
    justifyContent: "flex-end",
    alignItems: "center",
    marginTop: 12,
    gap: 8,
  },

  selectedCategoryContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 12,
    marginBottom: 12,
  },
  backButton: {
    width: 36,
    height: 36,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 8,
  },
  selectedCategoryTitle: {
    fontSize: 20,
    color: "#356879",
    fontWeight: "700",
  },

  pictogramsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "flex-start",
    gap: 10,
  },
  pictogramButton: {
    width: "31%",
    minHeight: 125,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 8,
    paddingVertical: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.07,
    shadowRadius: 2,
    elevation: 2,
  },

  fraseIACargando: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  fraseIASugerida: {
    marginTop: 8,
    marginBottom: 12,
    padding: 14,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#B9D1D7",
  },
  fraseIATitulo: {
    fontSize: 13,
    fontWeight: "700",
    color: "#356879",
    marginBottom: 6,
  },
  fraseIATexto: { fontSize: 14, lineHeight: 20, color: "#5F6B70" },
  fraseIABotones: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 12,
  },
  fraseIARechazar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 9,
    borderRadius: 9,
    backgroundColor: "#EEF3F5",
  },
  fraseIARechazarTexto: {
    color: "#5F6B70",
    fontSize: 11,
    fontWeight: "600",
  },
  fraseIAAceptar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 9,
    borderRadius: 9,
    backgroundColor: "#356879",
  },
  fraseIAAceptarTexto: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "700",
  },

  sugerenciasContainer: {
    marginTop: 0,
    marginBottom: 8,
    width: "100%",
  },
  sugerenciasTitulo: {
    color: "#789097",
    fontSize: 13,
    fontWeight: "600",
    marginBottom: 8,
    marginLeft: 2,
  },
  sugerenciasLista: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "flex-start",
    gap: 10,
  },
  sugerenciaChip: {
    width: "31%",
    minHeight: 82,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    paddingHorizontal: 8,
    paddingVertical: 8,
    borderWidth: 2,
    borderColor: "#D9C8C8",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
  },
  sugerenciaTexto: {
    color: "#356879",
    fontSize: 12,
    fontWeight: "600",
    textAlign: "center",
  },
  pictogramImage: { width: 75, height: 75, marginBottom: 5 },
  noImageContainer: {
    width: 75,
    height: 75,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 5,
  },
  pictogramText: {
    fontSize: 12,
    color: "#5F6B70",
    textAlign: "center",
    fontWeight: "600",
  },

  loadingContainer: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 35,
  },
  loadingText: { marginTop: 10, fontSize: 12, color: "#356879" },
  emptyPictogramsContainer: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 20,
    paddingHorizontal: 30,
  },
  emptyText: {
    marginTop: 10,
    fontSize: 12,
    color: "#7A898F",
    textAlign: "center",
  },

  newWordButton: {
    width: "31%",
    minHeight: 82,
    borderWidth: 1,
    borderColor: "#356879",
    borderRadius: 14,
    backgroundColor: "#FFFFFF",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 8,
    paddingVertical: 8,
  },
  newWordButtonText: {
    fontSize: 10,
    fontWeight: "600",
    marginTop: 4,
    textAlign: "center",
  },
  newWordContainer: {
    marginTop: 20,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 15,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.07,
    shadowRadius: 2,
    elevation: 2,
  },
  newWordTitle: {
    fontSize: 16,
    color: "#356879",
    fontWeight: "700",
    marginBottom: 10,
  },
  newWordInput: {
    height: 45,
    borderWidth: 1,
    borderColor: "#C8D3D7",
    borderRadius: 10,
    paddingHorizontal: 12,
    fontSize: 14,
    color: "#5F6B70",
    backgroundColor: "#F8FAFB",
  },
  imagePickerButton: {
    minHeight: 75,
    marginTop: 12,
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: "#B9C9CE",
    borderRadius: 12,
    backgroundColor: "#F8FAFB",
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    position: "relative",
  },
  imageIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: "#E8F1F3",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  imagePickerTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: "#356879",
  },
  imagePickerSubtitle: {
    fontSize: 11,
    color: "#7A898F",
    marginTop: 3,
  },
  selectedImage: {
    width: 55,
    height: 55,
    borderRadius: 10,
    marginRight: 10,
  },
  imageInfo: { flexDirection: "row", alignItems: "center", flex: 1 },
  imageSelectedText: {
    fontSize: 12,
    color: "#5F6B70",
    fontWeight: "600",
    marginLeft: 6,
    flex: 1,
  },
  removeImageButton: { padding: 3 },
  newWordButtons: {
    flexDirection: "row",
    justifyContent: "flex-end",
    alignItems: "center",
    marginTop: 12,
    gap: 8,
  },

  cancelButton: {
    paddingHorizontal: 15,
    paddingVertical: 9,
    borderRadius: 9,
    backgroundColor: "#EEF3F5",
  },
  cancelButtonText: {
    color: "#5F6B70",
    fontSize: 12,
    fontWeight: "600",
  },
  saveButton: {
    paddingHorizontal: 15,
    paddingVertical: 9,
    borderRadius: 9,
    backgroundColor: "#356879",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    minWidth: 80,
  },
  disabledButton: { opacity: 0.6 },
  saveButtonText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "700",
    marginLeft: 4,
  },
});
