var test_input = document.getElementById("test_input")
var button = document.getElementById("test_button")

button.addEventListener("click",()=>{
    console.log(test_input.value)
    console.log(typeof(test_input))
});