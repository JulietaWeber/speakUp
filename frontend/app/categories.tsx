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
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";

import ConstructionBar from "../components/ConstructionBar";
import { useConstruction } from "../context/ConstructionContext";

import {
  obtenerCategorias,
  obtenerPictogramasPorCategoria,
  crearCategoria,
  crearPictogramaPersonalizado,
} from "../services/api";

export default function Categories() {
  const { agregarPalabra } = useConstruction();

  const [categories, setCategories] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] =
    useState<any | null>(null);

  const [pictograms, setPictograms] = useState<any[]>([]);
  const [loadingPictograms, setLoadingPictograms] =
    useState(false);

  const [mostrarAgregarPalabra, setMostrarAgregarPalabra] =
    useState(false);

  const [nuevoNombre, setNuevoNombre] = useState("");

  const [mostrarAgregarCategoria, setMostrarAgregarCategoria] =
    useState(false);

  const [nuevoNombreCategoria, setNuevoNombreCategoria] =
    useState("");

  const [guardandoPalabra, setGuardandoPalabra] =
    useState(false);

  const [guardandoCategoria, setGuardandoCategoria] =
    useState(false);

  // =========================
  // CARGAR CATEGORÍAS
  // =========================

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
        console.error(
          "Error cargando categorías:",
          error
        );
      }
    };

    cargarCategorias();
  }, []);

  // =========================
  // CARGAR PICTOGRAMAS
  // =========================

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

        const data =
          await obtenerPictogramasPorCategoria(
            selectedCategory.id_categorias,
            token
          );

        setPictograms(data);
      } catch (error) {
        console.error(
          "Error cargando pictogramas:",
          error
        );

        setPictograms([]);
      } finally {
        setLoadingPictograms(false);
      }
    };

    cargarPictogramas();
  }, [selectedCategory]);

  // =========================
  // COLOR SUAVE
  // =========================

  const getBackgroundColor = (color: string) => {
    if (!color) {
      return "#F2F6F7";
    }

    if (color.startsWith("#")) {
      const hex = color.replace("#", "");

      const r = parseInt(
        hex.substring(0, 2),
        16
      );

      const g = parseInt(
        hex.substring(2, 4),
        16
      );

      const b = parseInt(
        hex.substring(4, 6),
        16
      );

      const softR = Math.round(
        r + (255 - r) * 0.78
      );

      const softG = Math.round(
        g + (255 - g) * 0.78
      );

      const softB = Math.round(
        b + (255 - b) * 0.78
      );

      return `rgb(${softR}, ${softG}, ${softB})`;
    }

    return "#F2F6F7";
  };

  // =========================
  // SELECCIONAR CATEGORÍA
  // =========================

  const seleccionarCategoria = (
    category: any
  ) => {
    setSelectedCategory(category);

    setMostrarAgregarPalabra(false);
    setNuevoNombre("");

    setMostrarAgregarCategoria(false);
    setNuevoNombreCategoria("");
  };

  // =========================
  // AGREGAR PICTOGRAMA A FRASE
  // =========================

  const agregarPictograma = (
    pictogram: any
  ) => {
    agregarPalabra(pictogram);
  };

  // =========================
  // CREAR NUEVA PALABRA
  // =========================

  const guardarNuevaPalabra = async () => {
    if (!nuevoNombre.trim()) {
      Alert.alert(
        "Falta el nombre",
        "Escribí el nombre de la nueva palabra."
      );

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

      const token =
        await AsyncStorage.getItem("token");

      if (!token) {
        Alert.alert(
          "Error",
          "No se encontró el token del usuario."
        );

        return;
      }

      const nuevaPalabra =
        await crearPictogramaPersonalizado(
          selectedCategory.id_categorias,
          nuevoNombre.trim(),
          token
        );

      setPictograms((prev) => [
        ...prev,
        nuevaPalabra,
      ]);

      setNuevoNombre("");
      setMostrarAgregarPalabra(false);

      Alert.alert(
        "Palabra agregada",
        `"${nuevaPalabra.nombre}" fue agregada a ${selectedCategory.nombre}.`
      );
    } catch (error: any) {
      console.error(
        "Error creando palabra:",
        error
      );

      console.error(
        "Respuesta backend:",
        error?.response?.data
      );

      Alert.alert(
        "Error",
        error?.response?.data?.error ||
          "No se pudo crear la nueva palabra."
      );
    } finally {
      setGuardandoPalabra(false);
    }
  };

  // =========================
  // CREAR NUEVA CATEGORÍA
  // =========================

  const guardarNuevaCategoria = async () => {
    if (!nuevoNombreCategoria.trim()) {
      Alert.alert(
        "Falta el nombre",
        "Escribí el nombre de la nueva categoría."
      );

      return;
    }

    try {
      setGuardandoCategoria(true);

      const token =
        await AsyncStorage.getItem("token");

      if (!token) {
        Alert.alert(
          "Error",
          "No se encontró el token del usuario."
        );

        return;
      }

      const nuevaCategoria =
        await crearCategoria(
          nuevoNombreCategoria.trim(),
          "#356879",
          token
        );

      setCategories((prev) => [
        ...prev,
        nuevaCategoria,
      ]);

      setSelectedCategory(nuevaCategoria);

      setPictograms([]);

      setNuevoNombreCategoria("");
      setMostrarAgregarCategoria(false);

      Alert.alert(
        "Categoría creada",
        `"${nuevaCategoria.nombre}" fue creada correctamente.`
      );
    } catch (error: any) {
      console.error(
        "Error creando categoría:",
        error
      );

      console.error(
        "Respuesta backend:",
        error?.response?.data
      );

      Alert.alert(
        "Error",
        error?.response?.data?.error ||
          "No se pudo crear la nueva categoría."
      );
    } finally {
      setGuardandoCategoria(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.keyboardContainer}
      behavior={
        Platform.OS === "ios"
          ? "padding"
          : "height"
      }
      keyboardVerticalOffset={
        Platform.OS === "ios" ? 0 : 0
      }
    >
      <View style={styles.container}>

        {/* =========================
            HEADER
        ========================= */}

        <View style={styles.header}>
          <Text style={styles.headerTitle}>
            Speak Up
          </Text>

          <TouchableOpacity
            style={styles.settingsButton}
          >
            <Ionicons
              name="settings-outline"
              size={25}
              color="#FFFFFF"
            />
          </TouchableOpacity>
        </View>

        {/* =========================
            CONTENIDO
        ========================= */}

        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode={
            Platform.OS === "ios"
              ? "interactive"
              : "on-drag"
          }
        >

          {/* =========================
              BARRA DE CONSTRUCCIÓN
          ========================= */}

          <ConstructionBar />

          {/* =========================
              TÍTULO CATEGORÍAS
          ========================= */}

          <Text style={styles.categoriesTitle}>
            Categorías
          </Text>

          {/* =========================
              CATEGORÍAS
          ========================= */}

          <View style={styles.categoriesContainer}>
            {categories.map((cat) => {
              const categoryColor =
                cat.color || "#356879";

              const backgroundColor =
                getBackgroundColor(
                  categoryColor
                );

              const isSelected =
                selectedCategory?.id_categorias ===
                cat.id_categorias;

              return (
                <TouchableOpacity
                  key={cat.id_categorias}
                  activeOpacity={0.75}
                  onPress={() =>
                    seleccionarCategoria(cat)
                  }
                  style={[
                    styles.categoryButton,
                    {
                      backgroundColor: isSelected
                        ? categoryColor
                        : backgroundColor,

                      borderColor:
                        categoryColor,
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.categoryText,
                      {
                        color: isSelected
                          ? "#FFFFFF"
                          : "#5F6B70",
                      },
                    ]}
                  >
                    {cat.nombre}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {/* =========================
              AGREGAR NUEVA CATEGORÍA
          ========================= */}

          {!mostrarAgregarCategoria && (
            <TouchableOpacity
              style={styles.newCategoryButton}
              activeOpacity={0.75}
              onPress={() =>
                setMostrarAgregarCategoria(
                  true
                )
              }
            >
              <Ionicons
                name="add-circle-outline"
                size={22}
                color="#356879"
              />

              <Text
                style={
                  styles.newCategoryButtonText
                }
              >
                Agregar nueva categoría
              </Text>
            </TouchableOpacity>
          )}

          {/* =========================
              FORMULARIO NUEVA CATEGORÍA
          ========================= */}

          {mostrarAgregarCategoria && (
            <View
              style={
                styles.newCategoryContainer
              }
            >
              <Text
                style={
                  styles.newCategoryTitle
                }
              >
                Nueva categoría
              </Text>

              <TextInput
                value={
                  nuevoNombreCategoria
                }
                onChangeText={
                  setNuevoNombreCategoria
                }
                placeholder="Escribí el nombre de la categoría"
                placeholderTextColor="#9AA8AD"
                style={
                  styles.newCategoryInput
                }
                returnKeyType="done"
              />

              <View
                style={
                  styles.newCategoryButtons
                }
              >
                <TouchableOpacity
                  style={styles.cancelButton}
                  activeOpacity={0.75}
                  onPress={() => {
                    setMostrarAgregarCategoria(
                      false
                    );

                    setNuevoNombreCategoria(
                      ""
                    );
                  }}
                >
                  <Text
                    style={
                      styles.cancelButtonText
                    }
                  >
                    Cancelar
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[
                    styles.saveButton,
                    guardandoCategoria &&
                      styles.disabledButton,
                  ]}
                  activeOpacity={0.75}
                  disabled={guardandoCategoria}
                  onPress={
                    guardarNuevaCategoria
                  }
                >
                  {guardandoCategoria ? (
                    <ActivityIndicator
                      size="small"
                      color="#FFFFFF"
                    />
                  ) : (
                    <>
                      <Ionicons
                        name="checkmark"
                        size={18}
                        color="#FFFFFF"
                      />

                      <Text
                        style={
                          styles.saveButtonText
                        }
                      >
                        Guardar
                      </Text>
                    </>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* =========================
              CATEGORÍA SELECCIONADA
          ========================= */}

          {selectedCategory && (
            <>
              <View
                style={
                  styles.selectedCategoryContainer
                }
              >
                <View
                  style={[
                    styles.selectedCategoryLine,
                    {
                      backgroundColor:
                        selectedCategory.color ||
                        "#356879",
                    },
                  ]}
                />

                <Text
                  style={
                    styles.selectedCategoryTitle
                  }
                >
                  {selectedCategory.nombre}
                </Text>
              </View>

              {/* =========================
                  PICTOGRAMAS
              ========================= */}

              {loadingPictograms ? (
                <View
                  style={
                    styles.loadingContainer
                  }
                >
                  <ActivityIndicator
                    size="large"
                    color="#356879"
                  />

                  <Text
                    style={
                      styles.loadingText
                    }
                  >
                    Cargando pictogramas...
                  </Text>
                </View>
              ) : (
                <>
                  {pictograms.length > 0 && (
                    <View
                      style={
                        styles.pictogramsContainer
                      }
                    >
                      {pictograms.map(
                        (pictogram) => (
                          <TouchableOpacity
                            key={
                              pictogram.id_pictogramas
                            }
                            activeOpacity={0.75}
                            style={
                              styles.pictogramButton
                            }
                            onPress={() =>
                              agregarPictograma(
                                pictogram
                              )
                            }
                          >
                            {pictogram.imagen_url ? (
                              <Image
                                source={{
                                  uri: pictogram.imagen_url,
                                }}
                                style={
                                  styles.pictogramImage
                                }
                                resizeMode="contain"
                              />
                            ) : (
                              <View
                                style={
                                  styles.noImageContainer
                                }
                              >
                                <Ionicons
                                  name="image-outline"
                                  size={35}
                                  color="#AAB7BC"
                                />
                              </View>
                            )}

                            <Text
                              style={
                                styles.pictogramText
                              }
                              numberOfLines={2}
                            >
                              {
                                pictogram.nombre
                              }
                            </Text>
                          </TouchableOpacity>
                        )
                      )}
                    </View>
                  )}

                  {pictograms.length ===
                    0 && (
                    <View
                      style={
                        styles.emptyPictogramsContainer
                      }
                    >
                      <Ionicons
                        name="images-outline"
                        size={45}
                        color="#AAB7BC"
                      />

                      <Text
                        style={
                          styles.emptyText
                        }
                      >
                        Esta categoría todavía
                        no tiene pictogramas
                      </Text>
                    </View>
                  )}

                  {/* =========================
                      AGREGAR NUEVA PALABRA
                  ========================= */}

                  {!mostrarAgregarPalabra && (
                    <TouchableOpacity
                      style={[
                        styles.newWordButton,
                        {
                          borderColor:
                            selectedCategory.color ||
                            "#356879",
                        },
                      ]}
                      activeOpacity={0.75}
                      onPress={() =>
                        setMostrarAgregarPalabra(
                          true
                        )
                      }
                    >
                      <Ionicons
                        name="add-circle-outline"
                        size={22}
                        color={
                          selectedCategory.color ||
                          "#356879"
                        }
                      />

                      <Text
                        style={[
                          styles.newWordButtonText,
                          {
                            color:
                              selectedCategory.color ||
                              "#356879",
                          },
                        ]}
                      >
                        Agregar nueva palabra
                      </Text>
                    </TouchableOpacity>
                  )}

                  {/* =========================
                      FORMULARIO NUEVA PALABRA
                  ========================= */}

                  {mostrarAgregarPalabra && (
                    <View
                      style={
                        styles.newWordContainer
                      }
                    >
                      <Text
                        style={
                          styles.newWordTitle
                        }
                      >
                        Nueva palabra
                      </Text>

                      <TextInput
                        value={nuevoNombre}
                        onChangeText={
                          setNuevoNombre
                        }
                        placeholder="Escribí una palabra"
                        placeholderTextColor="#9AA8AD"
                        style={
                          styles.newWordInput
                        }
                        returnKeyType="done"
                      />

                      <View
                        style={
                          styles.newWordButtons
                        }
                      >
                        <TouchableOpacity
                          style={
                            styles.cancelButton
                          }
                          activeOpacity={0.75}
                          onPress={() => {
                            setMostrarAgregarPalabra(
                              false
                            );

                            setNuevoNombre("");
                          }}
                        >
                          <Text
                            style={
                              styles.cancelButtonText
                            }
                          >
                            Cancelar
                          </Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                          style={[
                            styles.saveButton,
                            guardandoPalabra &&
                              styles.disabledButton,
                          ]}
                          activeOpacity={0.75}
                          disabled={
                            guardandoPalabra
                          }
                          onPress={
                            guardarNuevaPalabra
                          }
                        >
                          {guardandoPalabra ? (
                            <ActivityIndicator
                              size="small"
                              color="#FFFFFF"
                            />
                          ) : (
                            <>
                              <Ionicons
                                name="checkmark"
                                size={18}
                                color="#FFFFFF"
                              />

                              <Text
                                style={
                                  styles.saveButtonText
                                }
                              >
                                Guardar
                              </Text>
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
  keyboardContainer: {
    flex: 1,
  },

  container: {
    flex: 1,
    backgroundColor: "#EEF3F5",
  },

  scroll: {
    flex: 1,
  },

  content: {
    paddingHorizontal: 8,
    paddingTop: 10,
    paddingBottom: 180,
  },

  // =========================
  // HEADER
  // =========================

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

  // =========================
  // CATEGORÍAS
  // =========================

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

    shadowOffset: {
      width: 0,
      height: 1,
    },

    shadowOpacity: 0.08,
    shadowRadius: 2,

    elevation: 2,
  },

  categoryText: {
    fontSize: 12,
    textAlign: "center",
    fontWeight: "600",
  },

  // =========================
  // NUEVA CATEGORÍA
  // =========================

  newCategoryButton: {
    marginTop: 15,
    minHeight: 52,
    borderWidth: 2,
    borderColor: "#356879",
    borderRadius: 14,
    backgroundColor: "#FFFFFF",
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 15,
  },

  newCategoryButtonText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#356879",
    marginLeft: 7,
  },

  newCategoryContainer: {
    marginTop: 15,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 15,

    shadowColor: "#000",

    shadowOffset: {
      width: 0,
      height: 1,
    },

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

  newCategoryButtons: {
    flexDirection: "row",
    justifyContent: "flex-end",
    alignItems: "center",
    marginTop: 12,
    gap: 8,
  },

  // =========================
  // CATEGORÍA SELECCIONADA
  // =========================

  selectedCategoryContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 22,
    marginBottom: 12,
  },

  selectedCategoryLine: {
    width: 5,
    height: 28,
    borderRadius: 5,
    marginRight: 8,
  },

  selectedCategoryTitle: {
    fontSize: 20,
    color: "#356879",
    fontWeight: "700",
  },

  // =========================
  // PICTOGRAMAS
  // =========================

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

    shadowOffset: {
      width: 0,
      height: 1,
    },

    shadowOpacity: 0.07,
    shadowRadius: 2,

    elevation: 2,
  },

  pictogramImage: {
    width: 75,
    height: 75,
    marginBottom: 5,
  },

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

  // =========================
  // CARGANDO
  // =========================

  loadingContainer: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 35,
  },

  loadingText: {
    marginTop: 10,
    fontSize: 12,
    color: "#356879",
  },

  // =========================
  // SIN PICTOGRAMAS
  // =========================

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

  // =========================
  // NUEVA PALABRA
  // =========================

  newWordButton: {
    marginTop: 20,
    minHeight: 52,
    borderWidth: 2,
    borderRadius: 14,
    backgroundColor: "#FFFFFF",
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 15,
  },

  newWordButtonText: {
    fontSize: 14,
    fontWeight: "700",
    marginLeft: 7,
  },

  newWordContainer: {
    marginTop: 20,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 15,

    shadowColor: "#000",

    shadowOffset: {
      width: 0,
      height: 1,
    },

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

  newWordButtons: {
    flexDirection: "row",
    justifyContent: "flex-end",
    alignItems: "center",
    marginTop: 12,
    gap: 8,
  },

  // =========================
  // BOTONES
  // =========================

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

  disabledButton: {
    opacity: 0.6,
  },

  saveButtonText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "700",
    marginLeft: 4,
  },
});