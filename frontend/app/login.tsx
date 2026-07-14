import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
} from "react-native";
import { router } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { login } from "../services/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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

      Alert.alert("Éxito", `¡Bienvenido ${data.usuario.nombre}!`);

      router.push("/categories");

    } catch (error: any) {
      Alert.alert(
        "Error",
        error?.response?.data?.error || "No se pudo iniciar sesión"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: "#f4f7fb",
        justifyContent: "center",
        paddingHorizontal: 30,
      }}
    >
      <Text
        style={{
          fontSize: 42,
          fontWeight: "bold",
          color: "#219ebc",
          textAlign: "center",
        }}
      >
        Speak Up
      </Text>

      <Text
        style={{
          textAlign: "center",
          color: "#666",
          marginTop: 10,
          marginBottom: 50,
          fontSize: 17,
        }}
      >
        Comunicación accesible para todos
      </Text>

      <Text
        style={{
          marginBottom: 8,
          fontSize: 16,
          color: "#444",
        }}
      >
        Usuario o Email
      </Text>

      <TextInput
        placeholder="Ingresar usuario"
        value={email}
        onChangeText={setEmail}
        placeholderTextColor="#999"
        autoCapitalize="none"
        style={{
          backgroundColor: "white",
          padding: 18,
          borderRadius: 16,
          marginBottom: 20,
          fontSize: 16,
        }}
      />

      <Text
        style={{
          marginBottom: 8,
          fontSize: 16,
          color: "#444",
        }}
      >
        Contraseña
      </Text>

      <TextInput
        placeholder="Ingresar contraseña"
        value={password}
        onChangeText={setPassword}
        placeholderTextColor="#999"
        secureTextEntry
        style={{
          backgroundColor: "white",
          padding: 18,
          borderRadius: 16,
          marginBottom: 35,
          fontSize: 16,
        }}
      />

      <TouchableOpacity
        onPress={handleLogin}
        disabled={loading}
        style={{
          backgroundColor: "#219ebc",
          padding: 20,
          borderRadius: 18,
          alignItems: "center",
          marginBottom: 20,
          opacity: loading ? 0.7 : 1,
        }}
      >
        <Text
          style={{
            color: "white",
            fontSize: 18,
            fontWeight: "bold",
          }}
        >
          {loading ? "Ingresando..." : "Iniciar Sesión"}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={() => router.push("/register")}>
        <Text
          style={{
            textAlign: "center",
            color: "#219ebc",
            fontSize: 15,
          }}
        >
          ¿No tenés cuenta? Registrate
        </Text>
      </TouchableOpacity>
    </View>
  );
}