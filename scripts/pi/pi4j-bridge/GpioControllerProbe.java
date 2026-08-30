import com.pi4j.io.gpio.GpioController;
import com.pi4j.io.gpio.GpioFactory;
import com.pi4j.io.gpio.GpioPinDigitalInput;
import com.pi4j.io.gpio.Pin;
import com.pi4j.io.gpio.PinPullResistance;
import com.pi4j.io.gpio.RaspiGpioProvider;
import com.pi4j.io.gpio.RaspiPin;
import com.pi4j.io.gpio.RaspiPinNumberingScheme;

/** Exercises the same Pi4J-v1 high-level provider used by TSDash. */
public final class GpioControllerProbe {
    private GpioControllerProbe() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("usage: GpioControllerProbe <BCM GPIO number>");
        }

        int address = Integer.parseInt(args[0]);
        Pin pin = RaspiPin.getPinByAddress(address);
        if (pin == null) {
            throw new IllegalArgumentException("unknown BCM GPIO: " + address);
        }

        GpioFactory.setDefaultProvider(
            new RaspiGpioProvider(RaspiPinNumberingScheme.BROADCOM_PIN_NUMBERING)
        );
        GpioController controller = GpioFactory.getInstance();
        GpioPinDigitalInput input = controller.provisionDigitalInputPin(
            pin,
            "TurboExoKeyOnProbe",
            PinPullResistance.PULL_UP
        );

        Thread.sleep(150);
        System.out.printf("gpio=%d state=%s%n", address, input.getState());
        controller.shutdown();
    }
}
