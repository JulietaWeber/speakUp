import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
} from "react-native";

import { router } from "expo-router";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = () => {
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

    router.push("/categories");
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
        style={{
          backgroundColor: "#219ebc",
          padding: 20,
          borderRadius: 18,
          alignItems: "center",
        }}
      >
        <Text
          style={{
            color: "white",
            fontWeight: "bold",
            fontSize: 18,
          }}
        >
          Registrarse
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