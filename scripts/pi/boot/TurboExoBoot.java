import java.awt.AlphaComposite;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GraphicsDevice;
import java.awt.GraphicsEnvironment;
import java.awt.RadialGradientPaint;
import java.awt.RenderingHints;
import java.awt.event.ActionEvent;
import java.awt.geom.Ellipse2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import javax.imageio.ImageIO;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.SwingUtilities;
import javax.swing.Timer;

/** Lightweight full-screen handoff animation shown while TSDash starts. */
public final class TurboExoBoot extends JPanel {
    private static final long MIN_VISIBLE_MS = 7450;
    private static final long MAX_VISIBLE_MS = 7450;
    private static final long FADE_MS = 500;
    private final BufferedImage artwork;
    private final File readyFile;
    private final long started = System.nanoTime();
    private double fadeStartedMs = -1.0;

    private TurboExoBoot(BufferedImage artwork, File readyFile) {
        this.artwork = artwork;
        this.readyFile = readyFile;
        setBackground(Color.BLACK);
    }

    private static float clamp(double value) {
        return (float) Math.max(0.0, Math.min(1.0, value));
    }

    private static float smooth(double value) {
        float x = clamp(value);
        return x * x * (3.0f - 2.0f * x);
    }

    private static void quality(Graphics2D g) {
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION,
                RenderingHints.VALUE_INTERPOLATION_BICUBIC);
        g.setRenderingHint(RenderingHints.KEY_RENDERING,
                RenderingHints.VALUE_RENDER_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                RenderingHints.VALUE_ANTIALIAS_ON);
    }

    private static void radialGlow(Graphics2D g, float x, float y, float radius,
            Color center, Color edge) {
        g.setPaint(new RadialGradientPaint(x, y, radius,
                new float[] {0.0f, 0.22f, 1.0f},
                new Color[] {center, new Color(center.getRed(), center.getGreen(),
                    center.getBlue(), center.getAlpha() / 3), edge}));
        g.fill(new Ellipse2D.Float(x - radius, y - radius, radius * 2, radius * 2));
    }

    private static void drawFrame(Graphics2D g, BufferedImage artwork,
            int width, int height, double elapsedMs, float exit) {
        quality(g);
        g.setColor(Color.BLACK);
        g.fillRect(0, 0, width, height);

        // Keep the camera locked and fade the car in uniformly. A spatial wipe
        // makes the still artwork feel like it is moving across the display.
        float reveal = smooth((elapsedMs - 120.0) / 1150.0);
        int logoTop = (int) (height * 0.785);
        g.setClip(0, 0, width, logoTop);
        g.setComposite(AlphaComposite.SrcOver.derive(reveal * exit));
        g.drawImage(artwork, 0, 0, width, height, null);
        g.setClip(null);

        // Emerald charge blooms outward from the engine bay as the chassis wakes.
        float charge = smooth((elapsedMs - 500.0) / 450.0)
                * (1.0f - smooth((elapsedMs - 1550.0) / 700.0)) * exit;
        if (charge > 0.001f) {
            radialGlow(g, width * 0.57f, height * 0.48f, width * 0.24f,
                    new Color(21, 170, 105, (int) (92 * charge)),
                    new Color(0, 0, 0, 0));
        }

        // Both lamps fire with a quick warm ballast pulse, then settle.
        float lamps = smooth((elapsedMs - 1120.0) / 180.0) * exit;
        float pulse = (float) (0.78 + 0.22 * Math.sin(elapsedMs * 0.030));
        if (lamps > 0.001f) {
            float lampRadius = width * 0.047f;
            int alpha = (int) (210 * lamps * pulse);
            radialGlow(g, width * 0.483f, height * 0.505f, lampRadius,
                    new Color(255, 228, 161, alpha), new Color(0, 0, 0, 0));
            radialGlow(g, width * 0.746f, height * 0.500f, lampRadius,
                    new Color(255, 228, 161, alpha), new Color(0, 0, 0, 0));
        }

        // Fade the entire animation to black before handing the display to TSDash.
        if (exit < 1.0f) {
            g.setComposite(AlphaComposite.SrcOver.derive(1.0f - exit));
            g.setColor(Color.BLACK);
            g.fillRect(0, 0, width, height);
        }

        // Fade the complete EXOCET word in uniformly, then fade it on the same
        // ending curve as the car and lights.
        float title = smooth((elapsedMs - 1900.0) / 1000.0);
        int titleLeft = (int) (width * 0.275);
        int titleRight = (int) (width * 0.725);
        g.setClip(titleLeft, logoTop, titleRight - titleLeft, height - logoTop);
        g.setComposite(AlphaComposite.SrcOver.derive(title * exit));
        g.drawImage(artwork, 0, 0, width, height, null);
        g.setClip(null);
        g.setComposite(AlphaComposite.SrcOver);
    }

    @Override
    protected void paintComponent(Graphics graphics) {
        super.paintComponent(graphics);
        Graphics2D g = (Graphics2D) graphics.create();
        double elapsedMs = (System.nanoTime() - started) / 1_000_000.0;
        if (fadeStartedMs < 0.0 && elapsedMs >= MIN_VISIBLE_MS
                && (readyFile == null || readyFile.isFile()
                    || elapsedMs >= MAX_VISIBLE_MS)) {
            fadeStartedMs = elapsedMs;
        }
        float reveal = smooth((elapsedMs - 250.0) / 1050.0);
        float exit = fadeStartedMs < 0.0
                ? 1.0f
                : 1.0f - smooth((elapsedMs - fadeStartedMs) / FADE_MS);
        drawFrame(g, artwork, getWidth(), getHeight(), elapsedMs, exit);
        g.dispose();
    }

    private static void renderPreview(String artworkPath, String outputDir) throws Exception {
        BufferedImage artwork = ImageIO.read(new File(artworkPath));
        File directory = new File(outputDir);
        if (!directory.isDirectory() && !directory.mkdirs()) {
            throw new IOException("Unable to create preview directory: " + directory);
        }
        for (int frame = 0; frame < 240; frame++) {
            double elapsedMs = frame * (1000.0 / 30.0);
            float exit = 1.0f - smooth((elapsedMs - 7450.0) / FADE_MS);
            BufferedImage output = new BufferedImage(1920, 1280,
                    BufferedImage.TYPE_INT_RGB);
            Graphics2D g = output.createGraphics();
            drawFrame(g, artwork, 1920, 1280, elapsedMs, exit);
            g.dispose();
            ImageIO.write(output, "png", new File(directory,
                    String.format("frame-%04d.png", frame)));
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 3 && "--render".equals(args[0])) {
            renderPreview(args[1], args[2]);
            return;
        }
        if (args.length < 1 || args.length > 3) {
            System.err.println("usage: TurboExoBoot <artwork.png> [ready-file] [visible-file]");
            System.exit(2);
        }
        BufferedImage artwork = ImageIO.read(new File(args[0]));
        if (artwork == null) {
            throw new IllegalArgumentException("Unable to read artwork: " + args[0]);
        }

        GraphicsDevice display = GraphicsEnvironment
                .getLocalGraphicsEnvironment().getDefaultScreenDevice();
        Dimension size = display.getDefaultConfiguration().getBounds().getSize();
        File readyFile = args.length >= 2 ? new File(args[1]) : null;
        TurboExoBoot panel = new TurboExoBoot(artwork, readyFile);
        JFrame[] frameRef = new JFrame[1];
        SwingUtilities.invokeAndWait(() -> {
            JFrame frame = new JFrame("TurboExo");
            frame.setUndecorated(true);
            frame.setType(JFrame.Type.UTILITY);
            frame.setAlwaysOnTop(true);
            frame.setAutoRequestFocus(false);
            frame.setFocusableWindowState(false);
            frame.setBackground(Color.BLACK);
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.setContentPane(panel);
            frame.setSize(size);
            frame.setLocation(0, 0);
            display.setFullScreenWindow(frame);
            frame.setVisible(true);
            frame.toFront();
            frameRef[0] = frame;
        });
        JFrame frame = frameRef[0];

        if (args.length == 3) {
            try {
                new File(args[2]).createNewFile();
            } catch (IOException error) {
                System.err.println("Unable to create visible marker: " + error.getMessage());
            }
        }

        Timer timer = new Timer(33, (ActionEvent event) -> {
            frame.setAlwaysOnTop(true);
            frame.toFront();
            panel.repaint();
            double elapsedMs = (System.nanoTime() - panel.started) / 1_000_000.0;
            if (panel.fadeStartedMs >= 0.0
                    && elapsedMs >= panel.fadeStartedMs + FADE_MS + 50.0) {
                ((Timer) event.getSource()).stop();
                display.setFullScreenWindow(null);
                frame.dispose();
                System.exit(0);
            }
        });
        timer.start();
    }
}
