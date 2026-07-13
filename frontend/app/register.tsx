import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
} from "react-native";
import { router } from "expo-router";
import { register } from "../services/api";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!name.trim()) {
      Alert.alert("Error", "Ingresá tu nombre");
      return;
    }

    if (!email.trim()) {
      Alert.alert("Error", "Ingresá tu email");
      return;
    }

    if (!password.trim()) {
      Alert.alert("Error", "Ingresá una contraseña");
      return;
    }

    try {
      setLoading(true);

      const data = await register(name, email, password);

      console.log("Usuario registrado:", data);

      Alert.alert(
        "Éxito",
        "Usuario registrado correctamente."
      );

      router.replace("/login");
    } catch (error: any) {
      console.log("ERROR REGISTER:");
      console.log(error);
      console.log(error.response);
      console.log(error.response?.data);

      Alert.alert(
        "Error",
        JSON.stringify(error.response?.data || error.message)
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
          fontSize: 38,
          fontWeight: "bold",
          color: "#219ebc",
          textAlign: "center",
          marginBottom: 40,
        }}
      >
        Crear Cuenta
      </Text>

      <TextInput
        placeholder="Nombre"
        value={name}
        onChangeText={setName}
        style={{
          backgroundColor: "white",
          padding: 18,
          borderRadius: 16,
          marginBottom: 20,
        }}
      />

      <TextInput
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        style={{
          backgroundColor: "white",
          padding: 18,
          borderRadius: 16,
          marginBottom: 20,
        }}
      />

      <TextInput
        placeholder="Contraseña"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        style={{
          backgroundColor: "white",
          padding: 18,
          borderRadius: 16,
          marginBottom: 30,
        }}
      />

      <TouchableOpacity
        onPress={handleRegister}
        disabled={loading}
        style={{
          backgroundColor: "#219ebc",
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
          {loading ? "Registrando..." : "Registrarse"}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        onPress={() => router.push("/login")}
        style={{
          marginTop: 20,
        }}
      >
        <Text
          style={{
            textAlign: "center",
            color: "#219ebc",
          }}
        >
          Ya tengo cuenta
        </Text>
      </TouchableOpacity>
    </View>
  );
}