import com.pi4j.wiringpi.Gpio;

/** Minimal Pi4J-v1 digital-input smoke test for the TurboExo TSDash bridge. */
public final class GpioInputProbe {
    private GpioInputProbe() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("usage: GpioInputProbe <BCM GPIO number>");
        }

        int pin = Integer.parseInt(args[0]);
        int setup = Gpio.wiringPiSetupGpio();
        if (setup != 0) {
            throw new IllegalStateException("wiringPiSetupGpio failed: " + setup);
        }

        Gpio.pinMode(pin, Gpio.INPUT);

        Gpio.pullUpDnControl(pin, Gpio.PUD_UP);
        Thread.sleep(100);
        int pulledUp = Gpio.digitalRead(pin);

        Gpio.pullUpDnControl(pin, Gpio.PUD_DOWN);
        Thread.sleep(100);
        int pulledDown = Gpio.digitalRead(pin);

        Gpio.pullUpDnControl(pin, Gpio.PUD_OFF);

        System.out.printf("gpio=%d pull_up=%d pull_down=%d%n", pin, pulledUp, pulledDown);
        if (pulledUp != Gpio.HIGH || pulledDown != Gpio.LOW) {
            throw new IllegalStateException("GPIO did not follow internal pulls");
        }
    }
}
