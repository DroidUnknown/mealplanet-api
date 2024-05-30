const stripe = Stripe("pk_test_51MHNJ9GJsAxo6t6tHxpX2aK9LzsJcs3ect5QvOF2JV1codxPFkrOgqUBcegiTOz8ncgW4TMyTQdeWUgJkrjwyzuX00BSm6pz3q")
var clientSecret = document.getElementById("clientSecret").value
var successUrl = document.getElementById("successUrl").value
var errorUrl = document.getElementById("clientSecret").value
var elements = ""
function getPaymentIntent() {
    const appearance = {
    theme: 'stripe',
    variables: {
        colorPrimary: '#0570de',
        colorBackground: '#ffffff',
        colorText: '#30313d',
        colorDanger: '#df1b41',
        fontFamily: 'Ideal Sans, system-ui, sans-serif',
        spacingUnit: '2px',
        borderRadius: '4px',
    }
    }
    const options = {
    clientSecret: clientSecret,
    appearance: appearance,
    };
    try {
        elements = stripe.elements(options);
        const paymentElement = elements.create('payment');
        paymentElement.mount('#payment-element');
    } catch (err) {
      console.log(err);
    }
}
const form = document.getElementById('payment-form');
form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const {error} = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: successUrl,
      },
    });
  
    if (error) {
        // This point will only be reached if there is an immediate error when
        // confirming the payment. Show error to your customer (for example, payment
        // details incomplete)
        const messageContainer = document.querySelector('#error-message');
        messageContainer.textContent = error.message;
        console.log(messageContainer)
        window.location.href(errorUrl);
    } else {
        // Your customer will be redirected to your `return_url`. For some payment
        // methods like iDEAL, your customer will be redirected to an intermediate
        // site first to authorize the payment, then redirected to the `return_url`.
    }
});
getPaymentIntent()





