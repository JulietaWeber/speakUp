const multer = require("multer");

const storage = multer.memoryStorage();

const fileFilter = (req, file, callback) => {
  const tiposMimePermitidos = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/pjpeg"
  ];

  const extensionesPermitidas = ["jpg", "jpeg", "jfif", "png", "webp"];

  const extension = file.originalname
    .split(".")
    .pop()
    .toLowerCase();

  const mimePermitido = tiposMimePermitidos.includes(file.mimetype);
  const extensionPermitida = extensionesPermitidas.includes(extension);

  if (mimePermitido || extensionPermitida) {
    callback(null, true);
  } else {
    callback(
      new Error("Solo se permiten imágenes JPG, JPEG, JFIF, PNG o WEBP"),
      false
    );
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: 2 * 1024 * 1024
  }
});

module.exports = upload;