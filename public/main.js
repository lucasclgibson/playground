import Alpine from 'alpinejs'

window.Alpine = Alpine

const forms = {
    csat: {
        name: 'CSAT Demo form',
        elements: [
            {
                caption: 'Hi there',
                type: 'message'
            },
            {
                caption: 'How was your stay with us?',
                type: 'csat'
            },
            {
                caption: 'What did you think of the check-in experience?',
                type: 'thumbs'
            },
            {
                caption: 'Please tell us a little more about your experience',
                type: 'text'
            }
        ]
    }
};

Alpine.data('form', (form) => {
    return {
        input: null,
        form: forms[form],
        elements: [],
        index: 0,
        init() {
            this.form.elements.some((element, index) => {
                this.addElement(element);
                this.index = index;
                return element.type !== 'message';
            });
        },
        addElement(element) {
            this.elements.push(element);
        },
        current() {
            return this.elements[this.elements.length - 1];
        },
        submit(el = null) {
            this.addElement({
                caption: this.input,
                img: el?.src,
                sent: true
            });
            this.input = null;
            setTimeout(() => {
                let nextElement = this.form.elements[++this.index];
                nextElement ? this.addElement(nextElement) : this.endChat();
                this.$refs.elements_window.scrollTop = this.$refs.elements_window.scrollHeight;
            }, 300);
        },
        endChat() {
            this.addElement({
                format: 'end'
            });
        }
    };
});

Alpine.start();