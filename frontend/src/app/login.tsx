import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
  } from "react-native";
  
  import { router } from "expo-router";
  
  export default function Login() {
    return (
      <View
        style={{
          flex: 1,
          backgroundColor: "#f4f7fb",
          justifyContent: "center",
          paddingHorizontal: 30,
        }}
      >
        {/* TITULO */}
  
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
  
        {/* INPUT EMAIL */}
  
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
          placeholderTextColor="#999"
          style={{
            backgroundColor: "white",
            padding: 18,
            borderRadius: 16,
            marginBottom: 20,
            fontSize: 16,
          }}
        />
  
        {/* INPUT PASSWORD */}
  
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
  
        {/* BOTON LOGIN */}
  
        <TouchableOpacity
          onPress={() => router.push("/categories")}
          style={{
            backgroundColor: "#219ebc",
            padding: 20,
            borderRadius: 18,
            alignItems: "center",
            marginBottom: 20,
          }}
        >
          <Text
            style={{
              color: "white",
              fontSize: 18,
              fontWeight: "bold",
            }}
          >
            Iniciar Sesión
          </Text>
        </TouchableOpacity>
  
        {/* REGISTRO */}
  
        <TouchableOpacity
          onPress={() => router.push("/register")}
        >
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