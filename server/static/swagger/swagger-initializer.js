window.onload = function() {
	//<editor-fold desc="Changeable Configuration Block">
	// the following lines will be replaced by docker/configurator, when it runs in a docker-container
	// layout: "StandaloneLayout"
	// validatorUrl: "https://validator.swagger.io/validator"
	// validatorUrl: null
	window.ui = SwaggerUIBundle({
		url: "/openapi.json",
		dom_id: '#swagger-ui',
		layout: "BaseLayout",
		supportedSubmitMethods: ["options", "head", "get", "post", "put", "patch", "delete"],
		presets: [
			SwaggerUIBundle.presets.apis,
			SwaggerUIStandalonePreset
			],
		plugins: [
			SwaggerUIBundle.plugins.DownloadUrl
			],
		deepLinking: true,
		tryItOutEnabled: true,
		showExtensions: true,
		showCommonExtensions: true,
		defaultModelsExpandDepth: 0,
		displayOperationId: false,
		displayRequestDuration: true,
		"requestSnippetsEnabled": true,
		filter: false,
		validatorUrl: null
	});
	//</editor-fold>
};
