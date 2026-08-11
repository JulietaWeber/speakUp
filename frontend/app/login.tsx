import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { login } from "../services/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email.trim()) {
      Alert.alert("Error", "Ingresá tu usuario o email");
      return;
    }

    if (!password.trim()) {
      Alert.alert("Error", "Ingresá tu contraseña");
      return;
    }

    try {
      setLoading(true);

      const data = await login(email, password);

      console.log("Login exitoso:", data);

      await AsyncStorage.setItem(
        "token",
        data.token
      );

      await AsyncStorage.setItem(
        "usuario",
        JSON.stringify(data.usuario)
      );

      Alert.alert(
        "Éxito",
        `¡Bienvenido ${data.usuario.nombre}!`
      );

      router.push("/categories");

    } catch (error: any) {
      console.log("ERROR LOGIN:", error);
      console.log(
        "RESPUESTA ERROR:",
        error?.response?.data
      );

      Alert.alert(
        "Error",
        error?.response?.data?.error ||
          "No se pudo iniciar sesión"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: "#356071",
      }}
    >

      {/* PARTE AZUL DE ARRIBA */}
      <View
        style={{
          alignItems: "center",
          paddingHorizontal: 30,
          paddingTop: 150,
          paddingBottom: 120,
          backgroundColor: "#356071",
        }}
      >
        {/* TÍTULO */}
        <Text
          style={{
            fontSize: 36,
            fontWeight: "bold",
            color: "white",
            textAlign: "center",
          }}
        >
          Inicia sesión en una cuenta ya existente
        </Text>

      </View>

      {/* CONTAINER CELESTE */}
      <View
        style={{
          flex: 1,
          backgroundColor: "#AFD4E8",
          borderTopLeftRadius: 30,
          borderTopRightRadius: 30,
          paddingHorizontal: 30,
          paddingTop: 25,
          overflow: "hidden",
        }}
      >

        {/* BOTÓN DE GOOGLE */}
        <TouchableOpacity
          style={{
            backgroundColor: "#CFE6F1",
            padding: 18,
            borderRadius: 16,
            alignItems: "center",
            marginBottom: 20,
          }}
        >
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
            }}
          >
            <Ionicons
              name="logo-google"
              size={18}
              color="#356071"
            />

            <Text
              style={{
                color: "#356071",
                fontWeight: "bold",
                marginLeft: 10,
              }}
            >
              Continuar con Google
            </Text>
          </View>
        </TouchableOpacity>

        {/* SEPARACIÓN CON LA "O" */}
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginBottom: 20,
          }}
        >
          <View
            style={{
              flex: 1,
              height: 1,
              backgroundColor: "#356071",
            }}
          />

          <Text
            style={{
              color: "#356071",
              marginHorizontal: 12,
              fontSize: 14,
              fontWeight: "bold",
            }}
          >
            o
          </Text>

          <View
            style={{
              flex: 1,
              height: 1,
              backgroundColor: "#356071",
            }}
          />
        </View>

        <TextInput
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          placeholderTextColor="#356071"
          autoCapitalize="none"
          style={{
            backgroundColor: "#CFE6F1",
            padding: 18,
            borderRadius: 16,
            marginBottom: 20,
            fontSize: 16,
          }}
        />

        {/* CONTRASEÑA + OJITO */}
        <View
          style={{
            flexDirection: "row",
            marginBottom: 30,
          }}
        >
          <TextInput
            placeholder="Contraseña"
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!showPassword}
            placeholderTextColor="#356071"
            style={{
              flex: 1,
              backgroundColor: "#CFE6F1",
              padding: 18,
              borderTopLeftRadius: 16,
              borderBottomLeftRadius: 16,
              borderTopRightRadius: 0,
              borderBottomRightRadius: 0,
              fontSize: 16,
            }}
          />

          <TouchableOpacity
            onPress={() =>
              setShowPassword(!showPassword)
            }
            style={{
              width: 50,
              backgroundColor: "#CFE6F1",
              borderLeftWidth: 5,
              borderLeftColor: "#AFD4E8",
              borderTopRightRadius: 16,
              borderBottomRightRadius: 16,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Ionicons
              name={
                showPassword
                  ? "eye-outline"
                  : "eye-off-outline"
              }
              size={16}
              color="#356071"
            />
          </TouchableOpacity>
        </View>

        {/* BOTÓN INICIAR SESIÓN */}
        <TouchableOpacity
          onPress={handleLogin}
          disabled={loading}
          style={{
            backgroundColor: "#356071",
            padding: 20,
            borderRadius: 18,
            alignItems: "center",
            opacity: loading ? 0.7 : 1,
          }}
        >
          <Text
            style={{
              color: "white",
              fontWeight: "bold",
              fontSize: 18,
            }}
          >
            {loading
              ? "Ingresando..."
              : "Iniciar Sesión"}
          </Text>
        </TouchableOpacity>

        {/* CREAR CUENTA */}
        <TouchableOpacity
          onPress={() => router.push("/register")}
          style={{
            marginTop: 20,
          }}
        >
          <Text
            style={{
              textAlign: "center",
              color: "#356071",
            }}
          >
            No tenés una cuenta?{" "}
            <Text
              style={{
                textDecorationLine: "underline",
              }}
            >
              Crea una cuenta
            </Text>
          </Text>
        </TouchableOpacity>

      </View>
    </View>
  );
}