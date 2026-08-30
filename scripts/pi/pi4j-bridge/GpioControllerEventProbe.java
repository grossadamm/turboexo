import com.pi4j.io.gpio.GpioController;
import com.pi4j.io.gpio.GpioFactory;
import com.pi4j.io.gpio.GpioPinDigitalInput;
import com.pi4j.io.gpio.Pin;
import com.pi4j.io.gpio.PinPullResistance;
import com.pi4j.io.gpio.RaspiGpioProvider;
import com.pi4j.io.gpio.RaspiPin;
import com.pi4j.io.gpio.RaspiPinNumberingScheme;
import com.pi4j.io.gpio.event.GpioPinDigitalStateChangeEvent;
import com.pi4j.io.gpio.event.GpioPinListenerDigital;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** Proves that a provisioned input receives live state-change callbacks. */
public final class GpioControllerEventProbe {
    private GpioControllerEventProbe() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException(
                "usage: GpioControllerEventProbe <BCM GPIO number>"
            );
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
            "TurboExoKeyOnEventProbe",
            PinPullResistance.OFF
        );
        CountDownLatch transitions = new CountDownLatch(2);
        input.addListener(new GpioPinListenerDigital() {
            @Override
            public void handleGpioPinDigitalStateChangeEvent(
                    GpioPinDigitalStateChangeEvent event) {
                System.out.printf("event=%s%n", event.getState());
                System.out.flush();
                transitions.countDown();
            }
        });

        System.out.printf("initial=%s%n", input.getState());
        System.out.flush();
        boolean complete = transitions.await(10, TimeUnit.SECONDS);
        if (!complete) {
            throw new IllegalStateException("did not observe two state transitions");
        }
        // Pi4J v1's native interrupt worker is intentionally long-lived; exiting
        // the probe avoids waiting on that worker after the assertion has passed.
        System.exit(0);
    }
}
