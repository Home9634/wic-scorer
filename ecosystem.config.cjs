module.exports = {
  apps: [
    {
      name: "wic-scorer-api",
      script: "bash",
      args: "start-api.sh",
      cwd: __dirname,
      autorestart: true,
      watch: false,
    },
  ],
};
